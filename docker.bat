docker stop smartquiz-app  
docker rm smartquiz-app  
docker build -t smart-quiz:latest .
docker run -d --name smartquiz-app -p 8000:8000 -v E:/smart-quiz/data:/data smart-quiz:latest                                                            