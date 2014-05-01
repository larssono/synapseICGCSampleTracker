date;synapse query "select assignee, status from file where parentId=='syn2364746'"|tail -n+2|sed -e "s/\[u\'//g" -e "s/\'\]//g" |cut -f2-3|sort |uniq -c
