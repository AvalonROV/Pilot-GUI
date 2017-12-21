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
    
    def __init__(self):
        super(Window, self).__init__()
        
        self.initUI()
        self.string_formatter()
        # ------THREADING-----#
        self.thread = Worker()
        self.connect(self.thread, SIGNAL('Hello'), self.information)
        self.thread.start()

        #------UDP Connection-----#
        #recieve_socket.settimeout(1)
        #while (True):
        #    send_scoket.sendto(("UDP_auth".encode()), (HOST, send_port))
        #    print('sending...')
        #    try:
        #        if (recieve_socket.recv(1024).decode() == 'auth_acknowledged'):
        #            break
        #    except:
        #        pass
                # sleep(5)
        #print('Connected!')
        recieve_socket.setblocking(0)

    def initUI(self):

        title1_font = QFont("Arial", 16, QFont.Bold)
        #title2_font = QFont("Arial", 10, QFont.setUnderline(True))

        application_title = QLabel()                        #Create label
        application_title.setText("ROV Control Interface")  #Set Text
        application_title.setFont(title1_font)
        application_title.setAlignment(Qt.AlignCenter)      #Set Allignment

        self.LEDs_label = QLabel()
        self.LEDs_label.setText("LEDs")

        self.led1_label = QLabel()
        self.led1_label.setText("Spectrum")
        self.led2_label = QLabel()
        self.led2_label.setText("Lights")

        self.led1_indicator = QLabel()
        self.led2_indicator = QLabel()
        self.red_circle_indicator = QPixmap('red_circle.png')
        self.green_circle_indicator = QPixmap('green_circle.png')
        self.led1_indicator.setPixmap(self.red_circle_indicator)
        self.led2_indicator.setPixmap(self.red_circle_indicator)

        self.recieved_string_label = QLabel()
        self.recieved_string_label.setText("String Recieved from ROV")
        self.recieved_string_txtbox = QTextEdit()
        self.recieved_string_txtbox.setReadOnly(True)
        self.complete_recieved_string = ''

        self.user_input = QTextEdit()

        vbox = QVBoxLayout() #Create layout container
        vbox.addWidget(application_title)

        vbox.addWidget(self.LEDs_label)

        LEDs_hbox = QHBoxLayout()
        LEDs_hbox.addWidget(self.led1_label)
        LEDs_hbox.addWidget(self.led1_indicator)
        LEDs_hbox.addWidget(self.led2_label)
        LEDs_hbox.addWidget(self.led2_indicator)

        vbox.addLayout(LEDs_hbox)

        vbox.addWidget(self.recieved_string_label)
        #vbox.addWidget(self.recieved_string_txtbox)

        #vbox.addWidget(self.user_input)
        recieved_string_box = QHBoxLayout()
        recieved_string_box.addWidget(self.recieved_string_txtbox)
        recieved_string_box.addWidget(self.user_input)

        vbox.addLayout(recieved_string_box)

        self.setLayout(vbox)
        
        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Buttons')    
        self.show()

    #------------What is to follow should be moved into a seprate file----------------------------
    def string_formatter(self):
        # ------ Storing the values from the different axis on joystick------#
        self.X_Axis = my_joystick.get_axis(0)  # X_Axis- Axis 0
        self.Y_Axis = my_joystick.get_axis(1)  # Y_Axis - Axis 1
        self.Throttle = my_joystick.get_axis(2)
        self.Yaw = my_joystick.get_axis(3)
        self.Rudder = my_joystick.get_axis(4)
        self.funnel_CW_button = my_joystick.get_button(4)  # Button 5
        self.funnel_CCW_button = my_joystick.get_button(5)  # Button 6
        self.arm_open_button = my_joystick.get_button(6)  # Button 7
        self.arm_close_button = my_joystick.get_button(7)  # Button 8
        self.LED1_button = my_joystick.get_button(10)  # Button SE
        self.LED2_button = my_joystick.get_button(11)  # Button ST
        self.BT_button1 = my_joystick.get_button(0)
        self.BT_button2 = my_joystick.get_button(1)
        self.BT = 0

        if(self.BT_button1 == 1):
            self.BT = 1
        elif(self.BT_button2 == 1):
            self.BT = 2

        # self.Roll= my_joystick.get_button(0)

        self.funnel = 0
        self.arm = 0
        global LED1
        global LED2

        # ------ Thrusters Power
        self.power = 0.4
        self.fwd_factor = 400 * self.power
        self.side_factor = 400 * self.power
        self.yaw_factor = 200  # minimum drag

        # Account for double power in case of diagonals
        if ((self.X_Axis > 0.1 and self.Y_Axis < -0.1) or
                (self.X_Axis < -0.1 and self.Y_Axis > 0.1) or
                (self.X_Axis < -0.1 and self.Y_Axis < -0.1) or
                (self.X_Axis > 0.1 and self.Y_Axis > 0.1)):
            self.fwd_factor = 200 * self.power
            self.side_factor = 200 * self.power

        self.fwd_left_thruster = int(
            1500 - self.fwd_factor * self.Y_Axis - self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)
        self.fwd_right_thruster = int(
            1500 + self.fwd_factor * self.Y_Axis + self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)
        self.bck_left_thruster = int(
            1500 - self.fwd_factor * self.Y_Axis - self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)
        self.bck_right_thruster = int(
            1500 + self.fwd_factor * self.Y_Axis - self.side_factor * self.X_Axis + self.yaw_factor * self.Yaw)

        self.front_thruster = int(1500 + self.fwd_factor * self.Rudder)
        self.back_thruster = int(1500 + self.fwd_factor * self.Rudder)

        # ------Pitching code------
        if(self.Throttle>0.1 or self.Throttle<-0.1):
            self.front_thruster = int(1500 - self.fwd_factor * self.Throttle)
            self.back_thruster = int(1500 - self.fwd_factor * self.Throttle)
        # -------------------------


        if (self.funnel_CW_button == 1):
            self.funnel = 1
        elif (self.funnel_CCW_button == 1):
            self.funnel = 2

        if (self.arm_open_button == 1):
            self.arm = 1
        elif (self.arm_close_button == 1):
            self.arm = 2

        if (self.LED1_button == 1):
            sleep(0.2)
            if (LED1 == 1):
                LED1 = 0
                self.led1_indicator.setPixmap(self.red_circle_indicator)
            else:
                LED1 = 1
                self.led1_indicator.setPixmap(self.green_circle_indicator)

        if (self.LED2_button == 1):
            sleep(0.2)
            if (LED2 == 1):
                LED2 = 0
                self.led2_indicator.setPixmap(self.red_circle_indicator)
            else:
                LED2 = 1
                self.led2_indicator.setPixmap(self.green_circle_indicator)

        self.stringToSend = str([self.fwd_left_thruster, self.front_thruster, self.fwd_right_thruster,
                                 self.bck_right_thruster, self.back_thruster, self.bck_left_thruster,
                                 self.arm, self.funnel, self.BT_button1, LED2, self.BT])
        print(self.stringToSend)

    def information(self):
        # self.comma=","
        # ----- Collecting Self Parameters of Joystick----#
        name_joystick = my_joystick.get_name()  # Collects the pre-defined name of joystick
        number_axes = my_joystick.get_numaxes()  # Collects the pre-defined number of axis
        number_buttons = my_joystick.get_numbuttons()  # Collects the pre-defined number of buttons
        #self.txt1.setText(str(name_joystick))  # Displaying the information
        #self.txt2.setText(str(number_axes))  # in the required textboxes
        #self.txt3.setText(str(number_buttons))
        send_scoket.sendto((self.stringToSend.encode()), (HOST, send_port))  # The thing that we send
        try:
            recieved_string = recieve_socket.recv(1024).decode()
            self.complete_recieved_string += recieved_string + '\n'
            self.recieved_string_txtbox.setText(self.complete_recieved_string)
            #print(self.complete_recieved_string)
        except:
            pass

        # send_scoket.sendto(str(self.comma).encode(),(HOST,send_port))
        # -------------------------------------#

        # ---------Collecting the value of the Axis---------#
        #self.txt4.setText(str("{:>.2f}".format(my_joystick.get_axis(0))))
        #   send_scoket.sendto(str("{:>.2f}".format(my_joystick.get_axis(0))).encode(),(HOST,send_port))
        #self.txt5.setText(str("{:>.2f}".format(my_joystick.get_axis(1))))
        #  send_scoket.sendto(str("{:>.2f}".format(my_joystick.get_axis(1))).encode(),(HOST,send_port))
        #self.txt6.setText(str("{:>.2f}".format(my_joystick.get_axis(2))))
        # send_scoket.sendto(str("{:>.2f}".format(my_joystick.get_axis(2))).encode(),(HOST,send_port))
        #self.txt7.setText(str("{:>.2f}".format(my_joystick.get_axis(3))))
        # send_scoket.sendto(str("{:>.2f}".format(my_joystick.get_axis(3))).encode(),(HOST,send_port))
        #self.txt8.setText(str("{:>.2f}".format(my_joystick.get_axis(4))))
        # send_scoket.sendto(str("{:>.2f}".format(my_joystick.get_axis(4))).encode(),(HOST,send_port))
        # ---------------------------------------------------#

        # ------------------Collecting the value of Buttons--------------#
        #self.txt9.setText(str(my_joystick.get_button(0)))
        # send_scoket.sendto(str(my_joystick.get_button(0)).encode(),(HOST,send_port))
        #self.txt10.setText(str(my_joystick.get_button(1)))
        # send_scoket.sendto(str(my_joystick.get_button(1)).encode(),(HOST,send_port))
        #self.txt11.setText(str(my_joystick.get_button(2)))
        # send_scoket.sendto(str(my_joystick.get_button(2)).encode(),(HOST,send_port))
        #self.txt12.setText(str(my_joystick.get_button(3)))
        # send_scoket.sendto(str(my_joystick.get_button(3)).encode(),(HOST,send_port))
        #self.txt13.setText(str(my_joystick.get_button(4)))
        # send_scoket.sendto(str(my_joystick.get_button(4)).encode(),(HOST,send_port))
        #self.txt14.setText(str(my_joystick.get_button(5)))
        # send_scoket.sendto(str(my_joystick.get_button(5)).encode(),(HOST,send_port))
        #self.txt15.setText(str(my_joystick.get_button(6)))
        # send_scoket.sendto(str(my_joystick.get_button(6)).encode(),(HOST,send_port))
        #self.txt16.setText(str(my_joystick.get_button(7)))
        # send_scoket.sendto(str(my_joystick.get_button(7)).encode(),(HOST,send_port))
        #self.txt17.setText(str(my_joystick.get_button(8)))
        # send_scoket.sendto(str(my_joystick.get_button(8)).encode(),(HOST,send_port))
        #self.txt18.setText(str(my_joystick.get_button(9)))
        # send_scoket.sendto(str(my_joystick.get_button(9)).encode(),(HOST,send_port))
        #self.txt19.setText(str(my_joystick.get_button(10)))
        # send_scoket.sendto(str(my_joystick.get_button(10)).encode(),(HOST,send_port))
        #self.txt20.setText(str(my_joystick.get_button(11)))
        # send_scoket.sendto(str(my_joystick.get_button(11)).encode(),(HOST,send_port))
        # ----------------------------------------------------------------
        self.string_formatter()  # Calling the thruster value


"""This class is responsible for threading which means runnin two operations
simultaneously. It emits a signal to define when the above program shoudl be
updated"""

class Worker(QThread):

    def __init__(self):
        QThread.__init__(self, parent=app)

    def run(self):
        EXIT=False
        while not EXIT:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    EXIT=True
            self.emit(SIGNAL('Hello'))
            clock.tick(30) #This determines how fast the frames change per second
            #time.sleep(1)
        pygame.quit() # This is used to quit pygame and use any internal program within the python
        quit()

def main():
    
    ex = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
