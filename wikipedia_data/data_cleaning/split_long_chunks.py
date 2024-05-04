import sys

sys.path.append("../")
import re
from utils import scroll_pages, get_extracted_page_chunks, construct_text_from_chunk
from chunk_data import prepare_for_disk
import json
from tqdm import tqdm
import nltk

# from nltk.tokenize import sent_tokenize


import spacy

print("Loading spacy model")
nlp = spacy.load(
    "en_core_web_sm",
    disable=[
        "parser",
        "ner",
        "tagger",
        "textcat",
        "lemmatizer",
        "attribute_ruler",
        "tok2vec",
        "morphologizer",
    ],
)
nlp.add_pipe("sentencizer")
print("Loaded spacy model")

# nltk.download('punkt')

input_file = "../subsample_chunked.xml"
output_file = "../subsample_chunkeder.xml"
N_PAGES = 2357969
target_length = 512
max_length = 1024


def split_into_sentences(text: str):
    # return sent_tokenize(text)
    doc = nlp(text)
    return [sent.text for sent in doc.sents]


def split_into_sentences_artigianale(text: str):
    sentences = [t + "." for t in text.split(".") if len(t) > 0]
    if len(sentences) > 1:
        return sentences
    return [t + "," for t in text.split(",") if len(t) > 0]


def recursive_split_and_format(text: str, titles: list, max_length: int):
    if len(text) <= max_length:
        return [{"titles": titles, "text": construct_text_from_chunk(titles, text)}]
    chunks = []
    sentences = split_into_sentences(text)
    if len(sentences) == 1:
        sentences = split_into_sentences_artigianale(text)
    if len(sentences) == 1:
        print("Rubbish chunk")
        return []  # it's rubbish, discard it
    num_sentences = len(sentences)
    idx1 = min(int(num_sentences * 0.6), num_sentences - 2)
    idx2 = max(int(num_sentences * 0.4), 1)
    first_half = "".join(sentences[:idx1])
    second_half = "".join(sentences[idx2:])
    chunks.extend(recursive_split_and_format(first_half, titles, max_length))
    chunks.extend(recursive_split_and_format(second_half, titles, max_length))
    return chunks


if __name__ == "__main__":
    with open(input_file, "r") as f:
        with open(output_file, "w") as out:
            for page in tqdm(scroll_pages(f), total=N_PAGES):
                chunks = get_extracted_page_chunks(page)
                new_chunks = []
                for chunk in chunks:
                    last_paragraph = ""
                    text, titles = chunk["text"], chunk["titles"]
                    if len("".join(titles)) > 300:
                        print(
                            "Rubbish chunk"
                        )  # TODO: understand why this happens (HTML page has tags in it)
                        continue
                    paragraphs = text.split("\n")
                    s = ""
                    for paragraph in paragraphs:
                        s += paragraph + "\n"
                        if len(s) > target_length:
                            new_chunks.extend(
                                recursive_split_and_format(s, titles, max_length)
                            )
                            s = ""
                    if len(s) > 0:
                        new_chunks.extend(
                            recursive_split_and_format(s, titles, max_length)
                        )
                p = prepare_for_disk(new_chunks)
                out.write(p)
