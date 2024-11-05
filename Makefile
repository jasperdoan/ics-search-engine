all: run

run:
	clear

index:
	python indexer.py

clean:
	rm -rf index.json