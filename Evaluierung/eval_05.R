### Librarys, WD #####
library(jsonlite)
library(tidyverse)
library(readxl)
library(dplyr)
library(stringr)

setwd("C:/Users/morit/OneDrive/UNI/Master/SS22/PJ DS/Repo/PJ-DS-Chatbot/Evaluierung")

### Data Import #####

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
  mutate(., 
         suggestionCount = str_count(agentAnswerText, "\\.\\)"), #Zählen wie viele vorschlaege gemacht werden
         ) %>%
  # mutate(.,
  #        suggestions = toString(unlist(regmatches(agentAnswerText, gregexpr("[[:digit:]]+", agentAnswerText))))
  #        ) #%>%
  select(.,-agentAnswerText)


# test = "1.) Erstattung nach Infektionsschutzgesetz bei Tätigkeitsverbot/Quarantäne - Arbeitgeber/innen (329421) (Score: 12.087656)<br />2.) Entschädigung nach Infektionsschutzgesetz bei Tätigkeitsverbot/Quarantäne - Selbstständige (329424) (Score: 11.800799)"
# #test = "142"
# res = unlist(regmatches(test, gregexpr("[[:digit:]]+", test)))
# readr::parse_number(res[seq(2,length(res),2)])


# Services ####
# asdf
services = services_raw %>% 
  select(., c(id, name, description))

services$id = as.numeric(services$id)

# eval pairs ####

# Identifier für Questions
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

# Daten müssen sortiert seiN!!
delete_rows_without_following_service_selection = function(subsett,key){ 
  toDelete = c()
  for(row in nrow(subsett):1){
    if(subsett$documentId[row] != 0){
      break
    }else{
      toDelete = c(toDelete,row)
    }
  }
  if(length(toDelete)>0)
    subsett = subsett[-c(toDelete),]
  return(subsett)
}

# Daten müssen sortiert seiN!!
use_following_service = function(subsett, key){
  
  search_first_service_selection = function(subsett){
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
    return(my_nth(subsett$documentId))
  }
  
  for(row in nrow(subsett):1){
    #print(subsett)
    if(subsett$documentId[row] == 0){
      subsett$documentId[row] = search_first_service_selection(subsett[-seq(1,row),])
    }
  }
  
  return(subsett)
}

# TEST
#eval_pairs = eval_pairs %>% filter(., file == "20220131--quantEvalAllExcel.xlsx", dialogId == 397)
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
  arrange(., file,temp_id) %>%
  group_modify(., delete_rows_without_following_service_selection) %>%
  group_modify(., use_following_service)
  


### Export, FIlter #####
# bug wenn in by.x named der spalte verwendet wird
output = merge(eval_pairs,select(services, -description),by.x = 6, by.y = 1, all.x = TRUE)
output = output %>% 
  filter(., 
         suggestionCount > 1,
         !is.na(name)
         ) %>%
  arrange(., file,temp_id) %>%
  select(.,-temp_id)
write_csv2(output, file="eval.csv")

#names(services)[1] = "documentId"
#pruf = merge(output,services,by.x = 5, by.y = 1, all.x = TRUE)


