# Commute-Sense
This LLM-enabled application presents a REST API with a single endpoint to generate a report
of the weather conditions along a driving route between two addresses.

## Add API Keys
You will need to add three API keys to a "dev.env" file at the root of the project:
1. OpenCage, which is used to geocode the start and end locations.
    * https://opencagedata.com/
2. OpenRoute, which is used to get the directions between the start and end locations.
    * https://openrouteservice.org/
3. Openrouter.ai, which is used to generate the weather description using an LLM.
    * https://openrouter.ai/

The dev.env file should have the format:

```
OPENROUTER_AI_KEY=<key>
OPENCAGE_KEY=<key>
OPENROUTE_KEY=<key>
```
## Running
To run this app, you will need to install docker and docker-compose.  Then, just run the command `docker-compose up` from the directory where the docker-compose.yml file is located.  This will build the docker image and start the containers.  You can then access the app by going to `http://localhost:8000` in a web browser.

## Swagger UI
The swagger documentation for the API can be found at http://localhost:8000/docs#/

## Debugging with VSCode
To debug the application using Visual Studio Code with Docker, follow these steps:

1. **Open the Project in VSCode**: Open your cloned repository in Visual Studio Code.

2. **Install the Remote Development Extension Pack**: Ensure that you have the Remote Development extension installed in VSCode. This will allow you to attach a debugger to the Docker container.

3. **Configure VSCode for Docker Debugging**:
   - Create a `.vscode` directory in the root of your project if it doesn't exist.
   - Inside `.vscode`, create a `launch.json` file with the following configuration:

    ```json
    {
      "version": "0.2.0",
      "configurations": [
        {
          "name": "Python: Remote Attach",
          "type": "python",
          "request": "attach",
          "connect": {
            "host": "localhost",
            "port": 5678
          },
          "pathMappings": [
            {
              "localRoot": "${workspaceFolder}",
              "remoteRoot": "/app"
            }
          ]
        }
      ]
    }
    ```

4. **Start the Application in Debug Mode**:
   - Run the application using the following command:
     ```sh
     docker-compose -f docker-compose-debug.yml up
     ```

5. **Attach the Debugger**:
   - Open the Run and Debug sidebar in VSCode (Ctrl+Shift+D).
   - Select "Python: Remote Attach" from the dropdown menu.
   - Click on the green play button to start the debugger.
