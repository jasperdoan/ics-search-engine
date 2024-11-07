all: run

run:
	clear

index:
	python indexer.py

clean:
	rm -rf index.json
	rm -rf documents.json
	rm -rf partial_indexes/

app:
	python -m streamlit run .\main.py