all: run

run:
	clear

index:
	python indexer.py

clean:
	rm -rf partial_indexes/
	rm -rf range_indexes/
	rm -rf full_analytics/

app:
	python -m streamlit run .\main.py