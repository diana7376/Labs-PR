# Lab 1: HTTP File Server with TCP Sockets

## 1. Source Directory Structure

![Project source](photos/img_8.png)

Project source directory containing server.py, client.py, Dockerfile, and docker-compose.yml files.

## 2. Docker Configuration Files
![Dockerfile](photos/img_9.png)

![docker-compose](photos/img_2.png)

Docker configuration files defining the containerized HTTP server setup.


## 3. Starting the Container
![Starting HTTP server](photos/img_1.png)

Starting the HTTP server container using docker-compose.

![Docker containers](photos/img.png)


Docker containers running, visible in Docker Desktop.

## 4. Server Command in Container

![Server startup](photos%2Fimg_10.png)

Server startup logs showing it's serving files from the content directory specified as argument.

## 5. Served Directory Contents

![Content directory](photos/img_3.png)

Content directory structure with HTML files, PNG images, PDF files, and subdirectory for testing.

## 6. Browser Requests

![HTML file](photos/img_4.png)

Main page served successfully when accessed via browser.

![JPG file](photos/img_6.png)

JPG file successfully served and opened in browser.

![PDF image](photos/img_5.png)

PDF file successfully displayed when accessed directly.

![HTML file](photos/img_7.png)

HTML file displayed successfully and opened in browser. 



![404 non-existent](photos/img_12.png)
"404 Not Found" response for non-existent file request.

![404 Not Found](photos/img_13.png)

"404 Not Found" response for file with a different extension rather than .pdf, .png and .html.

## 7. Client Implementation

![Terminal command](photos/img_14.png)

Successful downloading PDF file using curl command in terminal. The command used was: 
```bash 
D:\apps\miniconda\python.exe client.py localhost 8080 doc1.pdf
```

![PDF file downloaded](photos/img_11.png)
Opened PDF file in browser.

## 8. Directory Listing

![HTML file](photos/img_4.png)

Auto-generated directory listing for the /content subdirectory showing clickable PDF files with parent directory navigation and `Go Back` button.


## 9. Friend's Server

![Main page](photos%2Fimg_10.jpg)

Successfully accessing my main page on another device.




