import tkinter as tk #for creating GUIs
from PIL import Image, ImageTk #for creating and manipulating images
import numpy as np #for all math operations


def pixel_position_transform():
    pass

#  Use this to create a transform so we don't have to do all this math on every
#  iteration, just place a pixel in a spot in pic automatically.
#  Then, we can use Cython to speed it up even further.
def calculate_pixel_positions(pic, data):
    # loop through beams
    for ith_beam in range(num_beams):
        # calculate the proper rotation of the disc
        this_beam_center = array_main_axis + int(ith_beam * (360 / num_beams))  # in compass degrees
        this_beam_center = 90 - this_beam_center  # in trig degrees
        this_beam_center = this_beam_center * np.pi / 180  # in radians

        # loop through time
        for jth_layer in range(int(disc_diameter / 2 * disc_aspect)):
            # calculate geometry for this arc/beam
            pixels_in_this_arc = int((disc_diameter / 2 - jth_layer) * 2 * np.pi / num_beams)
            data_center = int(np.size(data[jth_layer, :, ith_beam]) / 2)
            this_arc = data[jth_layer, data_center - int(pixels_in_this_arc / 2):data_center + int(pixels_in_this_arc / 2),
                       ith_beam]
            rads_per_step = 2 * np.pi / num_beams / pixels_in_this_arc
            start_rads = this_beam_center - 2 * np.pi / num_beams / 2

            this_pixel = [0, 0]

            # loop through frequencies in wedge
            for kth_pixel in range(this_arc.size):
                # calculate the location of this pixel. Doing a cylindrical to cartesian coordinates calc
                this_pixel[0] = int(disc_diameter / 2) - int((disc_diameter / 2 - jth_layer) * np.sin(start_rads + rads_per_step * kth_pixel))
                this_pixel[1] = int(disc_diameter / 2) - int((disc_diameter / 2 - jth_layer) * np.cos(start_rads + rads_per_step * kth_pixel))

                # place the pixel in the picture array
                pic[this_pixel[0] - 1, this_pixel[1] - 1] = this_arc[kth_pixel]

    return pic


if __name__ == "__main__":
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
    pixels_per_beam = int(disc_circ/num_beams) #number of pixels in the outside ring of the disc
    data = np.zeros((int(disc_diameter/2 * disc_aspect),pixels_per_beam+1,num_beams)) # actual data, to be better imported later
        #data(time,freq,beam) 3-D array

    loop_counter = 0
    while True: #how many times to test (eventually a while loop)
        loop_counter += 1
        print(loop_counter)

        #shift the old data down one
        for layer in range(int(disc_diameter/2*disc_aspect)-1,0,-1): #from the inside of the circle out
            data[layer,:,:] = data[layer-1,:,:]

        #log new data
        new_randoms = np.random.randint(0,2**8,size=data.shape[2])
        new_data = np.array([np.full(pixels_per_beam + 1, point) for point in new_randoms]).transpose()
        data[0,:,:] = new_data[:,:]

        #create new image from data
        pic = np.zeros((disc_diameter,disc_diameter))

        pic = calculate_pixel_positions(pic, data)

        #create the image from the data and add to the window
        pic = pic.flatten() #convert 2-D pic array to 1-D as required by pillow
        disc = Image.new('L',(disc_diameter,disc_diameter)) #create a new image
        disc.putdata(pic) #put the 1-D data array in the picture
        disc = ImageTk.PhotoImage(disc) #convert the image to one that can be used by tkinter
        panel1 = tk.Label(stack,image = disc).grid(row=0) #add the image to the window, same spot every time
        stack.update() #update the window




