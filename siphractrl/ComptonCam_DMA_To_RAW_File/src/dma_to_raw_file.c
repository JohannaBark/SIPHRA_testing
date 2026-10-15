/**
 * @file dma_to_raw_file.c
 *
 * @date 17 September 2020
 * @version 0.1
 * @brief Read DMA datas and write them in a file
 */

#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/time.h>
#include <stdbool.h>
#include <hiredis/hiredis.h>

#include "/home/ubuntu/repositories/KM_comptoncamdmas/files/comptoncamdmas.h"

typedef struct {
  bool debug;
  bool toggle;
  bool blocking;
  bool verbose;
  bool redis;
  char redis_prefix[256];
  redisContext *redis_context;

  char input_device_name[256];
  int input_device_handler;

  bool output_file_1_enable;
  char output_file_1_name[256];
  FILE *output_file_1_handler;

  bool output_file_2_enable;
  char output_file_2_name[256];
  FILE *output_file_2_handler;

  uint32_t max_block_size;
  uint32_t max_count;

  bool max_file_size_enable;
  uint32_t max_file_size;
  uint32_t file_name_id;
  
  uint32_t* data;

  char prefix_filename[256];  
} ConfigDMAToRaw, *pConfigDMAToRaw;

int configure_s2mm (int file_desc)
{
  int ret_val;
  uint32_t reg0a = 0xaa;
  uint32_t args_for_configure_s2mm[2];
  args_for_configure_s2mm[0] = (uint32_t) 0;
  args_for_configure_s2mm[1] = (uint32_t) &reg0a;

  ret_val = ioctl(file_desc, CONFIGURE_S2MM, &args_for_configure_s2mm[0]);

  return ret_val;
}

int manage_command_line (pConfigDMAToRaw pConfig, int argc, char * const* argv){
  int opt;
  
  while((opt = getopt(argc, argv, ":i:o:k:c:s:df:tbvr:")) != -1) {
    switch(opt) {
    case 'i':
      printf("input_device_name: %s\n", optarg);
      snprintf(pConfig->input_device_name, sizeof pConfig->input_device_name, "%s", optarg);
      break;
      
    case 'o':
      printf("output_file_1_name: %s\n", optarg);
      snprintf(pConfig->output_file_1_name, sizeof pConfig->output_file_1_name, "%s", optarg);
      pConfig->output_file_1_enable = true;
      break;
      
    case 'k':
      printf("output_file_2_name: %s\n", optarg);
      snprintf(pConfig->output_file_2_name, sizeof pConfig->output_file_2_name, "%s", optarg);
      pConfig->output_file_2_enable = true;
      break;

    case 'c':
      printf("max_count: %s\n", optarg);
      pConfig->max_count = atoi (optarg);
      break;

    case 's':
      printf("max_block_size: %s\n", optarg);
      pConfig->max_block_size = atoi (optarg);
      break;

    case 'd':
      printf("option debug ON\n");
      pConfig->debug = true;
      break;

    case 'f':
      printf("max_file_size: %s\n", optarg);
      pConfig->max_file_size = atoi (optarg);
      pConfig->max_file_size_enable = true;
      break;      

    case 'b':
      printf("WARN !!! option blocking read ON\n");
      pConfig->blocking = true;
      break;

    case 't':
      printf("WARN !!! toggle debug in kernel driver !!!!!!!!!!!\n");
      pConfig->toggle = true;
      break;

    case 'v':
      printf("verbose mode : ON\n");
      pConfig->verbose = true;
      break;

    case 'r':
      printf ("REDIS : ON\n");
      snprintf(pConfig->redis_prefix, sizeof pConfig->redis_prefix, "%s", optarg);
      pConfig->redis = true;
      break;

    case ':':
      printf("option needs a value\n");
      break;

    case '?':
      printf("unknown option: %c\n", optopt);
      break;
    }
  }
  return 0;
}

int set_a_redis_ex_string (pConfigDMAToRaw pConfig, char * prefix, char * register_name, char * ex, char * value) {
  //char tmp_rediscommand[300];
  redisReply *reply;
  //snprintf (tmp_rediscommand, sizeof tmp_rediscommand, "SET %s%s %s %s", prefix, register_name, ex, value);    
  reply = (redisReply *)redisCommand(pConfig->redis_context, "SET %s%s %s %s", prefix, register_name, ex, value);
  printf("SET: %s\n", reply->str);
  freeReplyObject(reply);
  return 0;
}

int set_a_redis_uint32_t (pConfigDMAToRaw pConfig, char * prefix, char * register_name, char * ex, uint32_t value) {
  //char tmp_rediscommand[300];
  redisReply *reply;
  //snprintf (tmp_rediscommand, sizeof tmp_rediscommand, "SET %s%s %s %lu", prefix, register_name, ex, (unsigned long) value);    
  reply = (redisReply *)redisCommand(pConfig->redis_context, "SET %s%s %s %lu", prefix, register_name, ex, (unsigned long) value);    
  printf("SET: %s\n", reply->str);
  freeReplyObject(reply);
  return 0;
}

int get_a_redis_string (pConfigDMAToRaw pConfig, char * prefix, char * register_name, char * result) {
  char tmp_rediscommand[300];
  redisReply *reply;
  snprintf (tmp_rediscommand, sizeof tmp_rediscommand, "GET %s%s", prefix, register_name);    
  reply = (redisReply *)redisCommand(pConfig->redis_context, tmp_rediscommand);
  printf("*Redis command (%s) -> server returned %s\n", tmp_rediscommand, reply->str);
  strcpy(result, reply->str);
  freeReplyObject(reply);
  return 0;
}

int get_a_redis_uint32_t (pConfigDMAToRaw pConfig, char * prefix, char * register_name, uint32_t * result) {
  char tmp_rediscommand[300];
  redisReply *reply;
  snprintf (tmp_rediscommand, sizeof tmp_rediscommand, "GET %s%s", prefix, register_name);    
  reply = (redisReply *)redisCommand(pConfig->redis_context, tmp_rediscommand);
  printf("*Redis command (%s) -> server returned %s\n", tmp_rediscommand, reply->str);
  *result = atoi (reply->str);
  freeReplyObject(reply);
  return 0;
}

int get_a_redis_bool (pConfigDMAToRaw pConfig, char * prefix, char * register_name, bool * result) {
  char tmp_rediscommand[300];
  redisReply *reply;
  snprintf (tmp_rediscommand, sizeof tmp_rediscommand, "GET %s%s", prefix, register_name);    
  reply = (redisReply *)redisCommand(pConfig->redis_context, tmp_rediscommand);
  printf("*Redis command (%s) -> server returned %s\n", tmp_rediscommand, reply->str);
  *result = atoi (reply->str);
  freeReplyObject(reply);
  return 0;
}

int configure_redis_context (pConfigDMAToRaw pConfig) {
  setbuf(stdout, NULL);
  setbuf(stderr, NULL);
  // Open up a connection to Redis
  char host[] = "127.0.0.1"; 
  int port    = 6379;
  
  pConfig->redis_context = redisConnect(host, port);
  if (pConfig->redis_context != NULL && pConfig->redis_context->err) {
    printf("Error: %sn", pConfig->redis_context->errstr);
    return -1;
  }
  else {
    printf("Redis server connected at %s:%d\n", host, port);
  }
  // Ping Redis server
  redisReply *reply;
  reply = (redisReply *)redisCommand(pConfig->redis_context,"PING");
  printf("Redis server PING returned %s (%s)\n", reply->str, (!(strcmp(reply->str, "PONG")) ? "SUCCESS" : "FAIL"));
  freeReplyObject(reply);
  return 0;
}

int manage_redis (pConfigDMAToRaw pConfig) {
  char output_dir_1[256];
  char output_dir_2[256];

  if (configure_redis_context (pConfig) < 0) {return -1;}
  
  get_a_redis_bool (pConfig, pConfig->redis_prefix, "_DMA_BLOCKING_MODE", &pConfig->blocking);
  get_a_redis_string (pConfig, pConfig->redis_prefix, "_DMA_INPUT", pConfig->input_device_name);
  get_a_redis_uint32_t (pConfig, pConfig->redis_prefix, "_DMA_MAX_FILE_SIZE", &pConfig->max_file_size);
  if (pConfig->max_file_size > 0) {
    pConfig->max_file_size_enable = true;
  }
  get_a_redis_uint32_t (pConfig, pConfig->redis_prefix, "_DMA_MAX_BLOCK_SIZE", &pConfig->max_block_size);
  get_a_redis_string (pConfig, "", "FSW_LOG_PREFIX", pConfig->prefix_filename);
  get_a_redis_string (pConfig, "", "DMA_OUTPUT_DIRECTORY_1", output_dir_1);
  get_a_redis_string (pConfig, "", "DMA_OUTPUT_DIRECTORY_2", output_dir_2);
  get_a_redis_bool (pConfig, "", "DMA_ENABLE_OUTPUT_DIRECTORY_1", &pConfig->output_file_1_enable);
  get_a_redis_bool (pConfig, "", "DMA_ENABLE_OUTPUT_DIRECTORY_2", &pConfig->output_file_2_enable);

  snprintf(pConfig->output_file_1_name, sizeof pConfig->output_file_1_name, "%s%s_%s", output_dir_1, pConfig->prefix_filename, pConfig->redis_prefix);
  snprintf(pConfig->output_file_2_name, sizeof pConfig->output_file_2_name, "%s%s_%s", output_dir_2, pConfig->prefix_filename, pConfig->redis_prefix);

  return 0;
}

int open_input_device (pConfigDMAToRaw pConfig) {
  pConfig->input_device_handler = open(pConfig->input_device_name, 0);
  if (pConfig->input_device_handler < 0) {
    printf ("Can't open device file: %s\n", pConfig->input_device_name);
    return -1;
  }
  else {
    printf ("Device file opened : %s\n", pConfig->input_device_name);
  }  
  return 0;
}

int open_new_outputs (pConfigDMAToRaw pConfig) {
  char tmp_output_file_name[268];

  pConfig->file_name_id += 1;
  
  if (pConfig->output_file_1_enable) {
    if (pConfig->output_file_1_handler != NULL) {
      fclose (pConfig->output_file_1_handler);
    }
    snprintf(tmp_output_file_name, sizeof tmp_output_file_name, "%s.%04d", pConfig->output_file_1_name, pConfig->file_name_id); 
    pConfig->output_file_1_handler = fopen(tmp_output_file_name, "a");
    if (pConfig->output_file_1_handler == NULL) {
      printf ("Can't open output file: %s\n", tmp_output_file_name);
      pConfig->output_file_1_enable = false;
    }
    else {
      printf ("Output file 1 opened : %s\n", tmp_output_file_name);
    }
  }
     
  if (pConfig->output_file_2_enable) {
    if (pConfig->output_file_2_handler != NULL) {
      fclose (pConfig->output_file_2_handler);
    }
    snprintf(tmp_output_file_name, sizeof tmp_output_file_name, "%s.%04d", pConfig->output_file_2_name, pConfig->file_name_id); 
    pConfig->output_file_2_handler = fopen(tmp_output_file_name, "a");
    if (pConfig->output_file_2_handler == NULL) {
      printf ("Can't open output file: %s\n", tmp_output_file_name);
      pConfig->output_file_2_enable = false;
    }
    else {
      printf ("Output file 2 opened : %s\n", tmp_output_file_name);
    }
  }
  if (!(pConfig->output_file_1_enable | pConfig->output_file_2_enable)) {
    return -1;
  }
  return 0;
}

int close_all (pConfigDMAToRaw pConfig) {
  free (pConfig->data);
  if (pConfig->output_file_1_enable) {
    fclose (pConfig->output_file_1_handler);
  }
  if (pConfig->output_file_2_enable) {
    fclose (pConfig->output_file_2_handler);
  }
  close (pConfig->input_device_handler);

  return 0;
}

int Init_DMA (pConfigDMAToRaw pConfig) {
    
  uint32_t args_for_ioctl[2];
  uint32_t size_to_write = 0;
  pConfig->data = (uint32_t*) calloc ((pConfig->max_block_size >> 2), sizeof (uint32_t));
  args_for_ioctl[0] = (uint32_t) &size_to_write;
  args_for_ioctl[1] = (uint32_t) pConfig->data;
  
  if (pConfig->toggle)
    {
      ioctl(pConfig->input_device_handler, TOGGLE_DEBUG, &args_for_ioctl[0]);
    }

  configure_s2mm (pConfig->input_device_handler);

  return 0;
}

int Read_DMA_And_Write_File (pConfigDMAToRaw pConfig) {
  struct timeval  tv1, tv2;
  uint32_t size_to_write = 0;
  uint32_t size_writen = 0;
  uint32_t counter = 0;
  uint32_t idx;
  
  uint32_t args_for_ioctl[2];
  args_for_ioctl[0] = (uint32_t) &size_to_write;
  args_for_ioctl[1] = (uint32_t) pConfig->data;


  do {
    gettimeofday (&tv1, NULL);

    size_to_write = pConfig->max_block_size;
    if (pConfig->blocking)
      {
        ioctl(pConfig->input_device_handler, BLOCKING_ALL_IN_ONE_READ, &args_for_ioctl[0]);
      }
    else
      {
        ioctl(pConfig->input_device_handler, ALL_IN_ONE_READ, &args_for_ioctl[0]);
      }

    if (size_to_write > 0) {

      if (pConfig->max_file_size_enable) {
	if (size_writen + size_to_write > pConfig->max_file_size) {
	  size_writen = 0;
	  if (open_new_outputs (pConfig) < 0) {
	    exit (-4);
	  }
	}
      }
      if (pConfig->output_file_1_enable) {
	fwrite (pConfig->data, sizeof (uint32_t), (size_to_write >> 2), pConfig->output_file_1_handler);
      }
      if (pConfig->output_file_2_enable) {
	fwrite (pConfig->data, sizeof (uint32_t), (size_to_write >> 2), pConfig->output_file_2_handler);
      }
      size_writen += size_to_write;
      
      if (pConfig->debug) {
        idx = 0;
        printf ("dma_to_raw_file: all_in_one_read : Data [%03u] = 0x%08x\n", idx, pConfig->data[idx]);
        idx = (size_to_write >> 2) - 1;
        printf ("dma_to_raw_file: all_in_one_read : Data [%03u] = 0x%08x\n", idx, pConfig->data[idx]);
      }
    }

    if (pConfig->verbose || size_to_write > 0) {
      gettimeofday (&tv2, NULL);

      printf ("%s : all_in_one_read : reg = 0x%x    %10d Total time = %f seconds\n",
	      pConfig->input_device_name,
	      size_to_write,
              counter,
              (double) (tv2.tv_usec - tv1.tv_usec) / 1000000 +
              (double) (tv2.tv_sec - tv1.tv_sec));

    }
    counter++;
  } while ((pConfig->max_count == 0)||(counter < pConfig->max_count));

  return 0;
}

int main(int argc, char *argv[])
{
  ConfigDMAToRaw Config =
    {.debug = false,
     .toggle = false,
     .blocking = false,
     .verbose = false,
     .redis = false,
     .output_file_1_enable = false,
     .output_file_2_enable = false,
     //.max_block_size = 16384,
     .max_block_size = 4095,
     .max_count = 0,
     .max_file_size_enable = false,
     .max_file_size = 0,
     .file_name_id = 0,
    };
  pConfigDMAToRaw pConfig = &Config;

  manage_command_line (pConfig, argc, argv);

  if (pConfig->redis){
    if (manage_redis (pConfig) < 0) {
      exit (-3);
    }
  }
  
  if (open_input_device (pConfig) < 0) {
    exit(-1);
  }

  if (open_new_outputs (pConfig) < 0) {
    exit (-2);
  }
  
  Init_DMA (pConfig);

  Read_DMA_And_Write_File (pConfig); 

  close_all (pConfig);

  return 0;
}
