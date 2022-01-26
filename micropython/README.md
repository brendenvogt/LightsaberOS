

# Helpful tools 
``` sh
function put() {
    for file in $@
    do
        echo "Putting $file"
        ampy put $file
    done
}
function deploy() {
    put $(ls *.py | xargs)
} 
```

### Deploy all files to device 
```sh
deploy
```

### Redeploying single file or multiple files
``` sh
put main.py
# or multiple files
put main.py i2c.py
```