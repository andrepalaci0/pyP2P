pra ver quais portas estao em uso 

sudo lsof -i -P -n | grep LISTEN

pra matar um processo

sudo kill -9 PID

pra rodar a instancia princial (no momento):
```bash
python3 src/main.py 127.0.0.1:5004 src/inputs/vizinhos.txt
```
Para rodar o resto da topologia:
```bash
./run.bash
```
