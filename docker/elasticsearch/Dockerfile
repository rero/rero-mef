FROM docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2
RUN bin/elasticsearch-plugin install analysis-icu

# German compound-word dictionary for the hyphenation_decompounder filter used
# by the concepts_mef/places_mef mappings. See analysis/NOTICE.txt for license
# and provenance (LGPL-v3+ dictionary, LPPL hyphenation patterns), vendored
# from https://github.com/uschindler/german-decompounder.
COPY analysis/dictionary-de.txt analysis/de_DR.xml config/analysis/
