# Link App – A Multi-Functional Communication Platform 

## Introduction
The Link App is a project aimed at developing an all-in-one communication platform that combines multiple features such as text chatting, voice calling, and file sharing into a single, easy-to-use application. This application will allow users to stay connected with a simple interface.

## Objective
The objective of the Link App is to create a user-friendly and feature-rich communication tool that allows users to chat, make voice calls, and share files. The platform is designed to be simple to use while providing high-quality and secure communication options.

## Key Features
The main features of the Link App include:
1. **Text Chat**: Real-time messaging with support for group chats.
2. **Voice Calling**: High-quality voice calls 
3. **File Sharing**: Secure and easy file transfers for images, documents, and videos.
## 4. Approach
I am using three separate sockets for chatting, file sharing, and voice calling.

## 5. Steps to Make This App
1. First, I made a simple chatting app using a TCP socket.
2. Then I separate made a voice calling app using UDP socket.
3. After it, I made a File sharing app using TCP socket.
4. In Final step, I merge the above three to Make a Link app.

## Technologies

1. **Frontend (GUI)**: Tkinter for desktop graphical user interface.
2. **Backend (Server)**: Python socket programming for real-time communication.
3. **WebRTC**: For voice calling.
4. **File Transfer Protocols**: HTTP/FTP for secure file sharing.
6. **Encryption**: SSL/TLS for secure communication and data transfer.
