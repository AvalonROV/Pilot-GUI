#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This code has been developed by Avalon ROV Team for participating in the MATE
ROV competition (https://www.marinetech.org/rov-competition-2/). This code is
a GUI used by the pilot in order to control the ROV and send/recieve important
information.
"""

#============== Imports ========================

import sys
from PyQt4.QtGui import*
from PyQt4.QtCore import *
import pygame
import socket
from time import sleep

#===============================================
#HOST = 'localhost'     # Used to test the code on the same computer
HOST = '192.168.1.5'    # Used to connect to the Arduino on board the ROV

send_port = 8000      # Defining the target send_port
recieve_port = 12345  # Defining the target recieve_port
"""
NOTE: The UDP connection does not allow for sending and recieving data on the
same port. For this reason two ports are used in this code for sending and
recieving data.
"""

send_scoket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP socket definition
recieve_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket definition
recieve_socket.bind(("", recieve_port)) # Bind the socket to the defined port

"""
PyGame is used to get and proces data from the joystick.
"""

pygame.init()   # Initialise PyGame
my_joystick = pygame.joystick.Joystick(0)   # Create a joystick object
my_joystick.init()  # Initialise the Joystick
clock = pygame.time.Clock() # Create a clock object to track time

app = QApplication(sys.argv) # Creat a new QApplication object. This manages
                             # the GUI application's control flow and main
                             # settings.

# Global variables defining the ROV LEDs status
LED1 = 0
LED2 = 0


class Window(QWidget):
    """
    This class is the base class of all user interface objects.
    """
    def __init__(self):
        super(Window, self).__init__()

        self.initUI()
        self.string_formatter()
        # ------THREADING-----#
        """
        This is used to process the joystick data in the background
        """
        self.thread = Worker()  #Define a thread object
        self.connect(self.thread, SIGNAL('Hello'), self.information) # Connect the incoming signal from the
                                                                     # thread to the 'information' function
        self.thread.start() #Start the thread

        recieve_socket.setblocking(0) #Stop the socket from blocking the code while awaiting data
                                      #In other words: set timeout to 0
    def initUI(self):

        #================ Definitions ========================
        title1_font = QFont("Arial", 16, QFont.Bold)    #Define title1 font

        # Title
        application_title = QLabel()                        #Create label for the window title
        application_title.setText("ROV Control Interface")  #Set Text
        application_title.setFont(title1_font)              #Set font
        application_title.setAlignment(Qt.AlignCenter)      #Set Allignment

        # LEDs
        self.LEDs_label = QLabel()              #Create label for the section title
        self.LEDs_label.setText("LEDs")         #Set Text

        self.led1_label = QLabel()              #Create label for LED1
        self.led1_label.setText("Spectrum")     #Set Text
        self.led2_label = QLabel()              #Create label for LED2
        self.led2_label.setText("Lights")       #Set Text

        self.led1_indicator = QLabel()          #Create label for LED1 indicator
        self.led2_indicator = QLabel()          #Create label for LED2 indicator
        self.red_circle_indicator = QPixmap('red_circle.png')       #Use an image of a red circle to indicate that the LEDs are off
        self.green_circle_indicator = QPixmap('green_circle.png')   #Use an image of a green circle to indicate that the LEDs are on
        self.led1_indicator.setPixmap(self.red_circle_indicator)
        self.led2_indicator.setPixmap(self.red_circle_indicator)

        self.recieved_string_label = QLabel()   #Create label for the text received from the ROV
        self.recieved_string_label.setText("String Recieved from ROV")  #Set Text
        self.recieved_string_txtbox = QTextEdit()   #Create a text box to store the data received from the ROV
        self.recieved_string_txtbox.setReadOnly(True)   #Set the text box to read only
        self.complete_recieved_string = ''

        self.user_input = QTextEdit()   #Create an empty text box for the pilot to write any notes


        #================ Layout ========================
        vbox = QVBoxLayout()                #Create layout container
        vbox.addWidget(application_title)   #Populate the container

        vbox.addWidget(self.LEDs_label)

        LEDs_hbox = QHBoxLayout()           #Create layout container
        LEDs_hbox.addWidget(self.led1_label)#Populate the container
        LEDs_hbox.addWidget(self.led1_indicator)
        LEDs_hbox.addWidget(self.led2_label)
        LEDs_hbox.addWidget(self.led2_indicator)

        vbox.addLayout(LEDs_hbox)

        vbox.addWidget(self.recieved_string_label)

        recieved_string_box = QHBoxLayout() #Create layout container
        recieved_string_box.addWidget(self.recieved_string_txtbox)  #Populate the container
        recieved_string_box.addWidget(self.user_input)

        vbox.addLayout(recieved_string_box)

        self.setLayout(vbox)    #Set the layout

        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Buttons')
        self.show()

    #------------What is to follow should be moved into a seprate file----------------------------
    def string_formatter(self):
        """
        This function formats the string that will be sent to the ROV containg the
        commands.

        The format of the string is: [FL, FU, FR, BR, BU, BL, ARM, FUN, LED1, LED2, BT]

        FL: Forward Left Thruster
        FU: Forward Up Thruster
        FR: Forward Right Thruster
        BR: Backward Right Thruster
        BU: Backward Up Thruster
        BL: Backward Left Thruster
        Thrusters values are between 1100 and 1900, with 1500 being nominal (at rest).

        ARM: Manipulator Arm
        FUN: Funnel
        0 -> not moving
        1 -> clockwise/opening
        2 -> anti-clockwise/closing

        LED1: On-baord LED
        LED2: On-baord LED
        0 -> OFF
        1 -> ON


        BT: Bluetooth
        """
        # ------ Storing the values from the different axis on joystick------#
        self.X_Axis = my_joystick.get_axis(0)  # X_Axis- Axis 0
        self.Y_Axis = my_joystick.get_axis(1)  # Y_Axis - Axis 1
        self.Throttle = my_joystick.get_axis(2)
        self.Yaw = my_joystick.get_axis(3)
        self.Rudder = my_joystick.get_axis(4)
        self.valve = my_joystick.get_button(4)  # Button 5

        self.CW_button = my_joystick.get_button(5)  # Button 6
        self.CCW_button = my_joystick.get_button(6)  # Button 7

        self.lift_bag = my_joystick.get_button(0)  # Button 1

        self.LED1_button = my_joystick.get_button(10)  # Button SE
        self.LED2_button = my_joystick.get_button(11)  # Button ST

        # Bluetooth controls
        self.BT_button1 = my_joystick.get_button(0)
        self.BT_button2 = my_joystick.get_button(1)

        # Initital values
        self.BT = 0
        self.stepper = 0
        self.arm = 0
        global LED1
        global LED2

        # ================================ Thrusters Power ================================
        """
        Power: Overall scaling factor (0.4 = 40% of the full power)
        Fwd_factor: The power factor when moving forward/backward
        Side_factor: The power factor when turning around (yaw)

        The values for the four thrusters in the horizontal plane (fwd_left_thruster,
        fwd_right_thruster, bck_left_thruster and bck_right_thruster) is calculated by
        taking in the value of each of the joystic three main control axis (X, Y and Yaw)
        values and multplying each value by the appropriate scaling factor. These values
        are then added with respect to the relevant sign (+ve/-ve).

        This is a reasonable approximation; however, this calculation has a limited
        domain at which it is valid. Specfically, at each of the four joystick diagonal
        axis (i.e: when X AND Y are equal to 1 or -1) the resultant value goes beyond the
        boundaries (1100 and 1900). Therefore, a condition has been written to handle this
        problem by dividing the resultant value by 2 (e.g: 3800 becomes 1900). This is not
        a perfect scenario but it is acceptable for this application.
        """
        self.power = 0.4
        self.fwd_factor = 400 * self.power
        self.side_factor = 400 * self.power
        self.yaw_factor = 200

        # Account for double power in case of diagonals
        if ((self.X_Axis > 0.1 and self.Y_Axis < -0.1) or
                (self.X_Axis < -0.1 and self.Y_Axis > 0.1) or
                (self.X_Axis < -0.1 and self.Y_Axis < -0.1) or
                (self.X_Axis > 0.1 and self.Y_Axis > 0.1)):
            self.fwd_factor = 200 * self.power      # multiply by half of the power factor
            self.side_factor = 200 * self.power

        self.fwd_left_thruster = int(
            1500 + self.fwd_factor * self.Y_Axis - self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)
        self.fwd_right_thruster = int(
            1500 - self.fwd_factor * self.Y_Axis + self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)
        self.bck_left_thruster = int(
            1500 - self.fwd_factor * self.Y_Axis - self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)
        self.bck_right_thruster = int(
            1500 - self.fwd_factor * self.Y_Axis - self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)


        # To go up/down
        self.front_thruster = int(1500 + self.fwd_factor * self.Rudder*-1)
        self.back_thruster = int(1500 + self.fwd_factor * self.Rudder)

        # ------Pitching code------
        """
        To pitch up/down the pilot needs to put the throttle in the +ve or -ve position. This overides
        the above 2 lines and moves the thrusters in oppsite directions in order to pitch as required.
        """
        if(self.Throttle>0.1 or self.Throttle<-0.1):
            self.front_thruster = int(1500 - self.fwd_factor * self.Throttle)
            self.back_thruster = int(1500 - self.fwd_factor * self.Throttle)


        # ================================ Manipulators ================================
        #stepper
        if (self.CW_button == 1):
            self.stepper = 1
        elif (self.CCW_button == 1):
            self.stepper = 2


        # LED1
        if (self.LED1_button == 1):
            sleep(0.2)
            if (LED1 == 1):
                LED1 = 0
                self.led1_indicator.setPixmap(self.red_circle_indicator)
            else:
                LED1 = 1
                self.led1_indicator.setPixmap(self.green_circle_indicator)

        # LED2
        if (self.LED2_button == 1):
            sleep(0.2)
            if (LED2 == 1):
                LED2 = 0
                self.led2_indicator.setPixmap(self.red_circle_indicator)
            else:
                LED2 = 1
                self.led2_indicator.setPixmap(self.green_circle_indicator)

        # Bluetooth
        if(self.BT_button1 == 1):
            self.BT = 1
        elif(self.BT_button2 == 1):
            self.BT = 2

        self.stringToSend = str([self.back_thruster, self.bck_left_thruster, self.bck_right_thruster,
                                 self.front_thruster, self.fwd_right_thruster, self.fwd_left_thruster,
                                 self.lift_bag, self.valve, self.stepper])

        # Final string to be sent
        # self.stringToSend = str([self.fwd_left_thruster, self.front_thruster, self.fwd_right_thruster,
        #                          self.bck_right_thruster, self.back_thruster, self.bck_left_thruster,
        #                          self.arm, self.stepper, self.BT_button1, LED2, self.BT])
        print(self.stringToSend) # Print final string

    def information(self):
        """
        This function reads parameters from the joystick and sends the formatted string to the ROV.
        """
        name_joystick = my_joystick.get_name()  # Collects the pre-defined name of joystick
        number_axes = my_joystick.get_numaxes()  # Collects the pre-defined number of axis
        number_buttons = my_joystick.get_numbuttons()  # Collects the pre-defined number of buttons
        send_scoket.sendto((self.stringToSend.encode()), (HOST, send_port))  # Send the string to the ROV

        try:    # Read data from the ROV
            recieved_string = recieve_socket.recv(1024).decode()
            self.complete_recieved_string += recieved_string + '\n'
            self.recieved_string_txtbox.setText(self.complete_recieved_string)
        except:
            pass

        self.string_formatter()  # Calling the thruster value


"""
This class is responsible for threading which means runnin two operations
simultaneously. It emits a signal to define when the above program should be
updated
"""

class Worker(QThread):

    def __init__(self):
        QThread.__init__(self, parent=app)

    def run(self):
        EXIT = False
        while not EXIT:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    EXIT = True
            self.emit(SIGNAL('Hello'))
            clock.tick(30) #This determines how fast the frames change per second
        pygame.quit() # This is used to quit pygame and use any internal program within the python
        quit()

def main():

    ex = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
