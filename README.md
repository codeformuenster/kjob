# kjob

```bash
sudo docker-compose up
```


```bash
sudo docker-compose run kjob bash


python kjob.py info

python kjob.py create --command test1
python kjob.py create --command test2
python kjob.py create --command test3
python kjob.py info

job=$(python kjob.py claim)
# echo "$job" | jq '.'
echo "$job"

# work something out

python kjob.py finish --job "$job" --result good
python kjob.py info
```
