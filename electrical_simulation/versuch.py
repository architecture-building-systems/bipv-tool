import pickle
import numpy
import pandas
import matplotlib.pyplot as plt


def align_yaxis(ax1, v1, ax2, v2):
    """adjust ax2 ylimit so that v2 in ax2 is aligned to v1 in ax1"""
    _, y1 = ax1.transData.transform((0, v1))
    _, y2 = ax2.transData.transform((0, v2))
    inv = ax2.transData.inverted()
    _, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
    miny, maxy = ax2.get_ylim()
    ax2.set_ylim(miny+dy, maxy+dy)



module_path_1 = r'F:\Paper\Module-simulations\orthogonal\electrical_simulation\results\module73.pkl'
module_path_2 = r'F:\Paper\Module-simulations\orthogonal\electrical_simulation_unbypassed\results\module73.pkl'
# module_path_3 = r'F:\Paper\Module-simulations\orthogonal\electrical_simulation_unbypassed\results\module10.pkl'
# module_path_4 = r'F:\Paper\Module-simulations\orthogonal\electrical_simulation\results\module32.pkl'
# module_path_5 = r'F:\Paper\Module-simulations\orthogonal\electrical_simulation\results\module74.pkl'
# module_path_6 = r'F:\Paper\Module-simulations\orthogonal\electrical_simulation\results\module73.pkl'

hour_of_year = 2434


with open(module_path_1) as datafile:
    module1_iv = pickle.load(datafile)
print "done"

with open(module_path_2) as datafile:
    module2_iv = pickle.load(datafile)
print "done"

# with open(module_path_3) as datafile:
#     module3_iv = pickle.load(datafile)
# print "done"
#
# with open(module_path_3) as datafile:
#     module3_iv = pickle.load(datafile)
# print "done"
#
# with open(module_path_4) as datafile:
#     module4_iv = pickle.load(datafile)
# print "done"
#
# with open(module_path_5) as datafile:
#     module5_iv = pickle.load(datafile)
# print "done"
#
# with open(module_path_6) as datafile:
#     module6_iv = pickle.load(datafile)
# print "done"

print len(module1_iv[hour_of_year][1])

plt.title("Module IV-curve")
plt.ylabel("current I [A]")
plt.xlabel("voltage V [V]")
plt.xlim(-10,60)
plt.ylim(-2,5)
plt.axvline(0.0, linewidth=1, linestyle='--', color='k')
plt.axhline(0.0, linewidth=1, linestyle='--', color='k')
ax = plt.gca()
ax2 = ax.twinx()
ax2.set_ylim(-20,120)
ax2.set_ylabel("Power P [W]")
ax.plot(module1_iv[hour_of_year][1],module1_iv[hour_of_year][0], label='with bypass diodes', color='orange')
ax.plot(module2_iv[hour_of_year][1],module2_iv[hour_of_year][0], label='without bypass diodes', color='g')
# ax.plot(module3_iv[hour_of_year][1],module3_iv[hour_of_year][0], label='IV curve newI')
# ax.plot(module4_iv[hour_of_year][1],module4_iv[hour_of_year][0], label='IV curve newII')
# ax.plot(module5_iv[hour_of_year][1],module5_iv[hour_of_year][0], label='IV curve clean')
# ax.plot(module6_iv[hour_of_year][1],module6_iv[hour_of_year][0], label='IV curve classic')
ax2.plot(module1_iv[hour_of_year][1], module1_iv[hour_of_year][0]*module1_iv[hour_of_year][1], color='r', label='bypassed')
ax2.plot(module2_iv[hour_of_year][1], module2_iv[hour_of_year][0]*module2_iv[hour_of_year][1], color='b', label='unbypassed')
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc='upper center')
handles, labels = ax2.get_legend_handles_labels()
ax2.legend(handles, labels, loc='upper right')
align_yaxis(ax, 0, ax2, 0)

# plt.savefig(r'F:\Animations\July04\module76/' + str(hour_of_year) + '.png')
plt.show()