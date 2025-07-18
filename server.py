from flask import Flask
import datetime

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/time')
def current_time():
    return f"Current time is: {datetime.datetime.now()}"

if __name__ == '__main__':
    app.run(debug=True)