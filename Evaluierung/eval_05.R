### Librarys, WD #####
library(jsonlite)
library(tidyverse)
library(readxl)
library(dplyr)
library(stringr)

setwd("C:/Users/morit/OneDrive/UNI/Master/SS22/PJ DS/Repo/PJ-DS-Chatbot/Evaluierung")

### Data Import #####

#TODO Weitere Dialogdaten

dialogues_raw = list()
for(file in list.files("dialogues")){
  dialogues_raw[[file]] = read_excel(paste("dialogues/",file,sep = "")) %>% mutate(file = file)
  
}
dialogues_raw = data.frame(do.call("rbind", dialogues_raw))

services_raw = fromJSON("dienstleistungen.json")$data


### Processing #####

# Dialoguees #####
keepColumns = c(
  "dialogId",
  "stateId",
  "dialogStatyType",
  "initialQuestion",
  "documentId",
  "agentAnswerText",
  "file"
)
dialogues = select(dialogues_raw, keepColumns)

statyTypes = c("QUESTION", "SERVICE_SELECTION", "SERVICES_ANSWER")

dialogues = dialogues %>% 
  filter(dialogStatyType %in% statyTypes) %>%
  group_by(dialogId,file) %>%
  # Nur dialoge mit ausgewähltem service
  # TODO kuerzen
  mutate(selection_happenend = sum(documentId)) %>% #ifelse(sum(documentId)>0,TRUE,FALSE)
  mutate(selection_happenend = ifelse(selection_happenend > 0, TRUE, FALSE)) %>%
  filter(selection_happenend == TRUE) %>% 
  select(.,-selection_happenend) %>%
  #
  mutate(., suggestionCount = str_count(agentAnswerText, "\\.\\)")) %>% # Zählen wie viele vorschlaege gemacht werden
  select(.,-agentAnswerText)

  
# Services ####
# asdf
services = services_raw %>% select(., c(id, name, description))

# eval pairs ####
#eval_pairs = merge(dialogues,services,by.x = "documentId",by.y= "id", all.x = TRUE) %>% arrange(., file,dialogId, stateId)
eval_pairs = dialogues %>% 
  arrange(., file, dialogId, stateId) %>%
  mutate(temp_id = 0)

z = 0
for(row in 1:nrow(eval_pairs)){
  if(eval_pairs$dialogStatyType[row] == "QUESTION"){
    z = z + 1
  }
  eval_pairs$temp_id[row] = z
}

my_nth = function(x){
  n = 1
  result = 0
  while(result==0){
    if(n> length(x)){
      break
    }else{
      result = dplyr::nth(x,n)
      n = n +1
    }
  }
  return(result)
}

eval_pairs = eval_pairs %>% 
  group_by(., dialogId, initialQuestion,temp_id, file) %>% 
  summarise(., 
            suggestionCount = sum(suggestionCount), 
            documentId = sum(documentId) #TODO gefährlich
            ) %>%
  mutate(.,directlyFound = ifelse(documentId != 0, TRUE, FALSE)) %>%
  ungroup(.) %>%
  #select(.,-temp_id) %>%
  group_by(., file, dialogId) %>%
  mutate(., documentId = my_nth(documentId)) %>%
  arrange(., file,temp_id)


### Beispiel FIlterung, CSV #####
output = eval_pairs %>% 
  filter(., suggestionCount > 1)

output = output %>% #merge(output,services,by.x = "documentId",by.y= "id", all.x = TRUE) %>% 
  arrange(., file,temp_id) %>%
  select(.,-temp_id)

write_csv2(output, file="eval.csv")