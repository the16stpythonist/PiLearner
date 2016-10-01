__author__ = "Jonas Teufel"
__version__ = "0.0.0"

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
import pisole.pisole as pisole
from ui import ExerciseCreation
from ui import MainMenu
from ui import ExamsMenu


class PiLearnerWidget(GridLayout):

    def __init__(self):
        super(PiLearnerWidget, self).__init__()

        self.cols = 4
        self.rows = 1
        self.minimum_height = 480
        self.minimum_width = 1150

        self.add_widget(ExamsMenu())
        self.add_widget(MainMenu(16))

        self.add_widget(ExerciseCreation("Elektronik", "Halbleiterphysik"))

        self.console = pisole.SimplePisoleConsole()
        self.console.start()
        self.add_widget(self.console.get_widget())

class PiLearnerApp(App):

    def build(self):
        return PiLearnerWidget()

if __name__ == "__main__":
    app = PiLearnerApp()
    app.run()