import numpy as np
import time
from operator import mul
from functools import reduce
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as mpatches
from subprocess import Popen, PIPE, STDOUT
import re
import os

basepath = os.path.abspath(os.path.dirname(__file__))

def set_axes_equal(ax,xmax,ymax,zmax):
    x_limits = (0,xmax)
    y_limits = (0,ymax)
    z_limits = (0,zmax)

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    plot_radius = 0.5*max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

def create_in_file(boxdim,items,item_dict,fname="cuboids.txt"):
    with open(fname,"w") as f:
        f.write(", ".join(map(str,boxdim))+"\n")
        for i,(it,num) in enumerate(items):
            f.write(str(i)+". "+", ".join(map(str,item_dict[it]))+", "+str(num))
            if it!=len(items)-1:
                f.write("\n")

def run_binary(fpath="cuboids",binpath="binpack.exe"):
    if os.path.exists(fpath+".out"):
        os.remove(fpath+".out")
    p = Popen([os.path.join(basepath,binpath)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    p.stdin.write((fpath+"\n").encode())

def decode_out_file(itemback,fpath="cuboids.out"):
    res = []
    while not os.path.exists(fpath):
        time.sleep(0.05)
    with open(fpath,"r") as f:
        lines = f.read().splitlines()
        for line in lines[17:]:
            if line.startswith("    "):
                info = list(map(int,re.split(r"\s+",line.strip())))
                res.append({
                    "name":itemback[tuple(info[2:5])],
                    "position":info[5:8],
                    "dimensions":info[8:11]
                })
            else:
                break
    return res

def visualize(boxdim,items,colormap,item_dict,divo=5):
    volsum = 0
    final_box = [0,0,0]
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_box_aspect([1.0, 1.0, 1.0])
    axes = np.array([boxdim[0],boxdim[1],boxdim[2]],dtype=int)//divo
    ax.set_xticks(np.arange(0,axes[0]+1,20//divo))
    ax.set_yticks(np.arange(0,axes[1]+1,20//divo))
    ax.set_zticks(np.arange(0,axes[2]+1,20//divo))
    ax.set_xticklabels(np.arange(0,boxdim[0]+1,divo*(20//divo)))
    ax.set_yticklabels(np.arange(0,boxdim[1]+1,divo*(20//divo)))
    ax.set_zticklabels(np.arange(0,boxdim[2]+1,divo*(20//divo)))
    data = np.zeros(axes, dtype=bool)
    colors = np.zeros(axes.tolist() + [4], dtype=np.float32)

    for item in items:
        volsum += reduce(mul,item["dimensions"])
        dim = np.array(item["dimensions"],dtype=int)//divo
        p = np.array(item["position"],dtype=int)//divo
        for i in range(3):
            final_box[i] = max(final_box[i],item["position"][i],item["position"][i]+item["dimensions"][i])
        colors[int(p[0]):int(dim[0]+p[0]),int(p[1]):int(dim[1]+p[1]),int(p[2]):int(dim[2]+p[2]),:] = np.array(colormap[item["name"]]+[160])/255
        data[int(p[0]):int(dim[0]+p[0]),int(p[1]):int(dim[1]+p[1]),int(p[2]):int(dim[2]+p[2])] = True

    patches = [mpatches.Patch(color=np.array(c)/255, label=n+" "+"x".join(map(str,item_dict[n]))) for n,c in colormap.items()]

    ax.voxels(data, facecolors=colors)
    set_axes_equal(ax,*axes)
    print("Container volume:",reduce(mul,boxdim))
    print("Items volume:",volsum)
    plt.title("Bounding box:"+"x".join(map(str,final_box)))
    plt.legend(handles=patches,bbox_to_anchor=(1.2,0.7))
    plt.show()

if __name__=="__main__":
    boxdim = (144,70,62)
    items = {'Kiste': (62, 35, 38),
            'PC-Kiste': (51,36,48),
            "Koffer":(61,40,26),
            'Wäschekorb': (49,29,27),
            'Werkzeugbox': (39,19,18),
            'Ikea Tüte': (40,24,18)}

    to_pack = [("Kiste",4),("PC-Kiste",1),("Koffer",1),("Wäschekorb",1),("Werkzeugbox",1),("Ikea Tüte",1)]

    item_reverse = {value:key for key,value in items.items()}

    colormap = {
        "Kiste":[125, 79, 6],
        "PC-Kiste":[0,0,0],
        "Wäschekorb":[100,100,100],
        "Werkzeugbox":[222, 222, 0],
        "Ikea Tüte":[0,0,255],
        "Koffer":[150,0,0],
    }


    create_in_file(boxdim,to_pack,items)
    run_binary()
    packed = decode_out_file(item_reverse)
    all_success = [x["name"] for x in packed]
    for n,p in to_pack:
        if all_success.count(n)!=p:
            print(f"WARNING, failed to pack {p-all_success.count(n)} {n}")
        
    visualize(boxdim,packed,colormap,items,5)

