# Commute-Sense

This app is designed to help users plan the best route to work by considering both transportation time and weather comfort.  It takes a start and end location as input and provides a list of directions to get from the start to the end, along with a weather report and a comfort score for each point on the route.  It also provides a summary of the overall route, including the total distance, time, and comfort score.

The app is intended to be used by anyone who is planning a commute and wants to know what the weather will be like for their trip.  It is particularly useful for people who are planning a trip to an unfamiliar location or who live in an area with variable weather conditions.  It is also useful for people who want to know how the weather will be at different points on their route, so they can plan their clothing and other preparations accordingly.

## Clone the Repository

To use the app, you will need to clone the repository by running the command `git clone https://github.com/commute-sense/commute-sense.git`.

## Add API Keys

You will need to add three API keys to the root of the directory:
1. OpenCage, which is used to geocode the start and end locations.
    * https://opencagedata.com/
    * file: opencage.key
2. OpenRoute, which is used to get the directions between the start and end locations.
    * https://openrouteservice.org/
    * file: openroute.key
3. Openrouter.ai, which is used to generate the weather description using an LLM.
    * https://openrouter.ai/
    * file: openrouter.ai.key

## Running

To run this app, you will need to install docker and docker-compose.  Then, just run the command `docker-compose up` from the directory where the docker-compose.yml file is located.  This will build the docker image and start the containers.  You can then access the app by going to `http://localhost:8000` in a web browser.

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

6. **Set Breakpoints and Debug**:
   - You can now set breakpoints in your Python code. The debugger will pause execution at these breakpoints, allowing you to inspect variables and step through the code.

By following these steps, you can effectively debug your application running inside a Docker container using VSCode.

