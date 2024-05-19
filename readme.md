pra ver quais portas estao em uso 

sudo lsof -i -P -n | grep LISTEN

pra matar um processo

sudo kill -9 <PID>