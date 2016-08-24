__author__ = "Jonas Teufel"
__version__ = "0.0.0"

from kivy.app import App
import pisole.pisole as pisole

class PiLearnerApp(App):

    def build(self):
        console = pisole.SimplePisoleConsole()
        console.start()
        return console.get_widget()

if __name__ == "__main__":
    app = PiLearnerApp()
    app.run()