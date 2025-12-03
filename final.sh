rm -rf final

mkdir final

# mkdir screenshots
mkdir final/screenshots

# copy screenshots
cp ./data/screenshots/* final/screenshots/

# copy all notebooks 
cp -r notebooks/* final/

# copy logs
cp *.log final/

# rm final/venv -rf
rm -rf final/venv

# create a zip file of the final directory
zip -r final_project.zip final/

