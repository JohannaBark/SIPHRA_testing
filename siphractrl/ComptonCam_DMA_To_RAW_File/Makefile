# Read DMA datas and write them in a file

CFLAGS = -g -Wall -Wextra -Wpedantic -pedantic -lhiredis

MAIN = dma_to_raw_file

all: $(MAIN)

$(MAIN): src/dma_to_raw_file.c
	$(CC) $^ -o $@ $(CFLAGS)

clean:
	find . -name "*.o" -delete
	find . -name "*~" -delete

distclean: clean
	$(RM) -rf $(MAIN)
