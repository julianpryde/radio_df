import tkinter as tk #for creating GUIs
from PIL import Image, ImageTk #for creating and manipulating images
import numpy as np #for all math operations

#Array Parameters
array_main_axis = 0 #direction of element 1 WRT the center
num_beams = 6 #number of azimuthal bins to display (for 3 or 4 elements, number of elements * 2)

#create window
stack = tk.Tk()
stack.title("Phased Array Display")
stack.geometry("1200x800")
stack.minsize(600,600)
stack.configure(background='black')

#RAZ Disc Parameters
disc_diameter = 500 #pixel diameter of RAZ disc
disc_aspect = 0.4 #fraction of the total disc radius to be filled with data
disc_circ = np.pi * disc_diameter #circumference of the disc outside edge
deg_per_beam = 360/num_beams #number of degrees per azimuthal bin
#following two parameters to be used for future integration of actual data and optimization
#scroll_speed = 10 #pixels per second
#sample_speed = 10 #samples per second

#Recieved Data
#displayed_Bandwidth = 16 #in MHz
pixels_per_beam = int(disc_circ/num_beams) #number of pizels in the outside ring of the disc
data = np.zeros((int(disc_diameter/2),pixels_per_beam+1,num_beams)) # actual data, to be better imported later
    #data(time,freq,beam) 3-D array

for i in range(300): #how many times to test (eventually a while loop)
    print(i)

    #shift the old data down one
    for layer in range(int(disc_diameter/2*disc_aspect)-1,0,-1): #from the inside of the circle out
        data[layer,:,:] = data[layer-1,:,:]
            
    #log new data
    new_data = np.random.randint(0,2**8,size=(data.shape[1],data.shape[2]))
    data[0,:,:] = new_data[:,:]

    #create new image from data
    pic = np.zeros((disc_diameter,disc_diameter))

    #loop through beams
    for a in range(num_beams):
        #calculate the proper roation of the disc
        this_beam_center = array_main_axis + int(a*(360/num_beams)) #in compass degrees
        this_beam_center = 90 - this_beam_center #in trig degrees
        this_beam_center = this_beam_center * np.pi / 180 #in radians

        #loop through time
        for b in range(int(disc_diameter/2*disc_aspect)):
            #calculate geometry for this arc/beam
            pixels_in_this_arc = int((disc_diameter/2 - b)*2*np.pi/num_beams)
            data_center = int(np.size(data[b,:,a])/2)
            this_arc = data[b,data_center-int(pixels_in_this_arc/2):data_center+int(pixels_in_this_arc/2),a]
            rads_per_step = 2*np.pi/num_beams/pixels_in_this_arc
            start_rads = this_beam_center - 2*np.pi/num_beams/2

            this = [0,0]
            #loop through frequencies in wedge
            for c in range(this_arc.size):
                #calculate the location of this pixel. Doing a cylindrical to cartesian coordinates calc
                this[0] = int(disc_diameter/2) - int((disc_diameter/2 - b) * np.sin(start_rads + rads_per_step * c))
                this[1] = int(disc_diameter/2) - int((disc_diameter/2 - b) * np.cos(start_rads + rads_per_step * c))

                #place the pixel in the picture array
                pic[this[0]-1,this[1]-1] = this_arc[c]
                

    #create the image from the data and add to the window
    pic = pic.flatten() #convert 2-D pic array to 1-D as required by pillow
    disc = Image.new('L',(disc_diameter,disc_diameter)) #create a new image
    disc.putdata(pic) #put the 1-D data array in the picture
    disc = ImageTk.PhotoImage(disc) #convert the image to one that can be used by tkinter
    panel1 = tk.Label(stack,image = disc).grid(row=0) #add the image to the window, same spot every time
    stack.update() #update the window




