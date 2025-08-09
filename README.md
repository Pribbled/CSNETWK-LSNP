# <p align="center">LNSP CLIENT</p>


This project is a Local Social Networking Protocol (LSNP) command-line client that handles sending and receiving messages over UDP. 
It supports various interactive commands such as posting messages, liking content, direct messaging, managing groups, playing Tic Tac Toe, file transfers, and handling authentication tokens.
---------------------------------------  

<br><br><br><br>


## Features

- **Post, DM, Like, and Unlike**
-> Receives and dispatches messages to the correct handlers based on message type.

- **Group Management**
-> Create, join, update, message, and leave groups.

- **Tic Tac Toe Game**
-> Invite, move, and quit games directly in the command line.

- **File Transfer**
-> Offer, accept, send, and receive files over the LSNP protocol.

- **Token Management**
-> Issue, revoke, and manage access tokens.

- **Verbose Mode**
-> Features detailed incoming/outgoing message logs for debugging.


## How To Run
1. Install all required files.
2. Ensure all module and handler files are present, and in the same folder.
3. In your command line, run the command: *python main.py*

## Included Files
- *socket_handler* – Socket creation.

- *message* – Parsing raw message data.

- *state* – Global State Variables.

- *utils* – Utility/Helper functions.

- *config* – Configuration settings.

- *handlers* – Individual message-type handlers.

- *file_transfer* – Functions for file handling.

<br><br><br><br>
---
### This project was developed in partial fulfillment of the requirements for the CSNETWK Machine Project by Group 5.
