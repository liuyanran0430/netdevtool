# 02-IRF命令参考

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-104514435.htm -->

mad enable命令用来开启LACP MAD方式检测功能。

undo mad enable用来关闭LACP MAD方式检测功能。

【命令】

mad enable

undo mad enable

【缺省情况】

LACP MAD检测功能处于关闭状态。

【视图】

聚合接口视图

【缺省用户角色】

network-admin

【使用指导】

LACP MAD和ARP MAD、ND MAD冲突处理的原则不同，请不要同时配置。

LACP MAD检测方式需要使用H3C设备作为中间设备，每个成员设备都需要连接到中间设备。请在动态聚合接口下开启LACP MAD方式检测功能。聚合接口创建后，可使用link-aggregation mode dynamic命令将该接口配置为动态接口。

在LACP MAD检测组网中，如果中间设备本身也是一个IRF系统，则必须通过配置确保其IRF域编号与被检测的IRF系统不同，否则可能造成检测异常，甚至导致业务中断。

为了防止IRF级联组网时，本IRF的MAD检测报文转发到邻居IRF中影响邻居IRF的MAD检测，执行mad enable命令时，系统会要求用户输入IRF域编号。如果继续使用当前编号，则直接按回车即可。

IRF域编号是一个全局变量，在IRF设备上使用irf domain、mad enable、mad arp enable、mad nd enable命令均可修改全局IRF域编号，最新的配置生效。

【举例】

\# 在二层动态聚合接口1下启用LACP MAD方式检测功能。

<Sysname> system-view

[Sysname] interface bridge-aggregation 1

[Sysname-Bridge-Aggregation1] link-aggregation mode dynamic

[Sysname-Bridge-Aggregation1] mad enable

 You need to assign a domain ID (range: 0-4294967295)

 [Current domain is: 0]: 1

 The assigned domain ID is: 1

MAD LACP only enable on dynamic aggregation interface.

\# 在三层动态聚合接口1下启用LACP MAD方式检测功能。

<Sysname> system-view

[Sysname] interface route-aggregation 1

[Sysname-Route-Aggregation1] link-aggregation mode dynamic

[Sysname-Bridge-Aggregation1] mad enable

 You need to assign a domain ID (range: 0-4294967295)

 [Current domain is: 0]: 1

 The assigned domain ID is: 1

MAD LACP only enable on dynamic aggregation interface.

【相关命令】

· irf domain


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-1150604181.htm -->

easy-irf命令用于快速配置IRF。

【命令】

easy-irf [ member member-id [ renumber new-member-id ] domain domain-id [ priority priority ] [ irf-port1 interface-list1 ] [ irf-port2 interface-list2 ] ]

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

member member-id：表示设备当前的成员编号，取值范围为1~10。

renumber new-member-id：表示新成员编号，取值范围为1~10。如果给成员设备指定新的成员编号，该成员设备会立即自动重启，以使新的成员编号生效。如果不指定该参数，则表示不修改成员编号。

domain domain-id：表示设备所属的IRF域编号，domain-id的取值范围为0～4294967295。同一IRF中的成员设备应配置相同的域编号。

priority priority：表示IRF成员的优先级，priority的取值范围为1～32。优先级值越大表示优先级越高，优先级高的设备竞选时成为主设备的可能性越大。

irf-port1 interface-list1：表示与IRF端口1绑定的IRF物理端口。表示方式为interface-list1 = { interface-type interface-number }&<1-8>。其中interface-type interface-number表示接口类型和接口编号。&<1-8>表示前面的参数最多可以输入8次。

irf-port2 interface-list2：表示与IRF端口2绑定的IRF物理端口。表示方式为interface-list2 = { interface-type interface-number }&<1-8>。其中interface-type interface-number表示接口类型和接口编号。&<1-8>表示前面的参数最多可以输入8次。同一物理端口只能一个IRF端口绑定。

【使用指导】

使用该功能，用户可以通过一条命令配置IRF的基本参数，包括新成员编号、域编号、绑定物理端口，简化了配置步骤，达到快速配置IRF的效果。

在配置该功能时，有两种方式：

· 交互模式：用户输入easy-irf，回车，在交互过程中输入具体参数的值。

· 非交互模式，在输入命令行时直接指定所需参数的值。

两种方式的配置效果相同，如果用户对本功能不熟悉，建议使用交互模式。

多次执行本命令时，生效情况如下：

· 多次执行本命令来修改域编号或优先级时，最近一次执行的命令生效。

· 多次执行本命令来修改IRF物理端口时，本次配置的端口会与之前已配置的端口同时生效。一个IRF端口最多可绑定8个IRF物理端口。

在交互模式下为IRF端口指定物理端口时，请注意：

· 接口类型和接口编号间不能有空格。

· 不同物理接口之间用英文逗号分隔，逗号前后不能有空格。

如需删除现有的IRF物理端口配置，需要在IRF端口视图下，执行undo port group interface命令。

更多配置要求，请参见“IRF配置指导”中的“IRF”。

【举例】

\# 通过非交互模式配置成员设备2的新成员编号为3，域编号为10，优先级为10，IRF端口1和Ten-GigabitEthernet2/0/1、Ten-GigabitEthernet2/0/2、Ten-GigabitEthernet2/0/3和Ten-GigabitEthernet2/0/4绑定。

<Sysname> system-view

[Sysname] easy-irf member 2 renumber 3 domain 10 priority 10 irf-port1 ten-gigabitethernet 2/0/1 ten-gigabitethernet 2/0/2 ten-gigabitethernet 2/0/3 ten-gigabitethernet 2/0/4

*****************************************************************************

 Configuration summary for member 2

IRF new member ID: 3

IRF domain ID: 10

IRF priority: 10

IRF-port 1: Ten-GigabitEthernet2/0/1, Ten-GigabitEthernet2/0/2

 Ten-GigabitEthernet2/0/3, Ten-GigabitEthernet2/0/4

IRF-port 2: Disabled

*****************************************************************************

Are you sure to use these settings to set up IRF? [Y/N] y

Starting to configure IRF...

Configuration succeeded.

The device will reboot for the new member ID to take effect. Continue? [Y/N] y

\# 通过交互模式配置成员设备3的新编号为5，域编号为10，优先级为10，IRF端口1和Ten-GigabitEthernet3/0/1、Ten-GigabitEthernet3/0/2、Ten-GigabitEthernet3/0/3和Ten-GigabitEthernet3/0/4绑定。

<Sysname> system-view

[Sysname] easy-irf

*****************************************************************************

Welcome to use easy IRF.

To skip the current step, enter a dot sign (.).

To return to the previous step, enter a minus sign (-).

To use the default value (enclosed in []) for each parameter, press Enter withou

t entering a value.

To quit the setup procedure, press CTRL+C.

*****************************************************************************

Select a member by its ID <3> [3]:3

Specify a new member ID <1~10> [1]: 5

Specify a domain ID <0~4294967295> [0]: 10

Specify a priority <1~32> [1]: 10

Specify IRF-port 1 bindings (a physical interface or a comma-separated physical

interface list)[Disabled]: ten-gigabitethernet3/0/1,ten-gigabitethernet3/0/2,ten-gigabitethernet3/0/3,ten-gigabitethernet3/0/4

Specify IRF-port 2 bindings (a physical interface or a comma-separated physical

interface list)[Disabled]:

*****************************************************************************

 Configuration summary for member 3

IRF new member ID: 5

IRF domain ID: 10

IRF priority: 10

IRF-port 1: Ten-GigabitEthernet3/0/1, Ten-GigabitEthernet3/0/2

 Ten-GigabitEthernet3/0/3, Ten-GigabitEthernet3/0/4

IRF-port 2: Disabled

*****************************************************************************

Are you sure to use these settings to set up IRF? [Y/N] y

Starting to configure IRF...

Configuration succeeded.

The device will reboot for the new member ID to take effect. Continue? [Y/N] y


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-1255794510.htm -->

irf auto-update enable命令用来开启IRF启动文件自动加载功能。

undo irf auto-update enable命令用来关闭IRF启动文件自动加载功能。

【命令】

irf auto-update enable

undo irf auto-update enable

【缺省情况】

IRF启动文件的自动加载功能处于开启状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

开启启动文件自动加载功能后，当新加入IRF的设备和主设备的软件版本不同时，新加入的设备会自动同步主设备的软件版本，再重新加入IRF。为了能够成功进行自动加载，请确保从设备存储介质上有足够的空闲空间用于存放IRF的启动文件。如果从设备存储介质上空闲空间不足，该设备将自动删除当前启动文件来再次尝试加载；如果空闲空间仍然不足，该从设备将无法进行自动加载。此时，需要管理员重启从设备并进入从设备的Boot ROM菜单，删除一些不重要的文件后，再将从设备重新加入IRF。

【举例】

\# 开启启动文件自动加载功能。

<Sysname> system-view

[Sysname] irf auto-update enable


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-1356839285.htm -->

mad nd enable命令用来开启ND MAD检测功能。

undo mad nd enable用来关闭ND MAD检测功能。

【命令】

mad nd enable

undo mad nd enable

【缺省情况】

ND MAD检测功能处于关闭状态。

【视图】

VLAN接口视图

【缺省用户角色】

network-admin

【使用指导】

ND MAD、ARP MAD和LACP MAD冲突处理的原则不同，请不要同时配置。

ND MAD、ARP MAD和BFD MAD冲突处理的原则不同，并且ND MAD、ARP MAD需要开启生成树协议，BFD MAD和生成树协议互斥，因此ND MAD、ARP MAD和BFD MAD无法同时配置。

VLAN 1不能用于MAD检测，因此，不能在VLAN接口1下开启ND MAD检测功能。

在ND MAD检测组网中，如果中间设备本身也是一个IRF系统，则必须通过配置确保其IRF域编号与被检测的IRF系统不同，否则可能造成检测异常，甚至导致业务中断。

为了防止IRF级联组网时，本IRF的MAD检测报文转发到邻居IRF中影响邻居IRF的MAD检测，执行mad nd enable命令时，系统会要求用户输入IRF域编号。如果继续使用当前编号，则直接按回车即可。

IRF域编号是一个全局变量，在IRF设备上使用irf domain、mad enable、mad arp enable、mad nd enable命令均可修改全局IRF域编号，最新的配置生效。

【举例】

\# 在VLAN接口3上启用ND MAD检测功能。

<Sysname> system-view

[Sysname] interface vlan-interface 3

[Sysname-Vlan-interface3] mad nd enable

 You need to assign a domain ID (range: 0-4294967295)

 [Current domain is: 0]: 1

 The assigned domain ID is: 1

【相关命令】

· irf domain


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-1486758368.htm -->

display irf-port load-sharing mode命令用来显示IRF链路的负载分担模式。

【命令】

display irf-port load-sharing mode [ irf-port [ member-id/irf-port-number ] ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

irf-port：显示指定IRF链路的负载分担模式。不指定该参数时，显示全局IRF链路的负载分担模式。

member-id/irf-port-number：表示IRF端口编号。其中，member-id表示设备在IRF中的成员编号；irf-port-number表示IRF端口索引，取值为1或2。不指定该参数时，显示所有连通的IRF链路的负载分担模式，如果当前没有连通的IRF链路，则显示“No IRF link exists.”。

【举例】

\# 显示缺省情况下全局采用的IRF链路负载分担模式。

<Sysname> display irf-port load-sharing mode

irf-port Load-Sharing Mode:

Layer 2 traffic: packet type-based sharing

Layer 3 traffic: packet type-based sharing

\# 显示非缺省情况下全局采用的IRF链路负载分担模式。

<Sysname> display irf-port load-sharing mode

irf-port Load-Sharing Mode:

destination-mac address, source-mac address

\# 显示缺省情况下IRF端口1/1下采用的负载分担模式。

<Sysname> display irf-port load-sharing mode irf-port 1/1

irf-port1/1 Load-Sharing Mode:

Layer 2 traffic: packet type-based sharing

Layer 3 traffic: packet type-based sharing

\# 显示非缺省情况下IRF端口1/1下采用的负载分担模式。

<Sysname> display irf-port load-sharing mode irf-port 1/1

irf-port 1/1 Load-Sharing Mode:

destination-mac address, source-mac address

\# 显示所有IRF端口下分别采用的负载分担模式。

<Sysname> display irf-port load-sharing mode irf-port

irf-port1/1 Load-Sharing Mode:

destination-mac address source-mac address

irf-port1/2 Load-Sharing Mode:

destination-ip address source-ip address

表1-5 display irf-port load-sharing mode命令显示信息描述表

| destination-mac address, source-mac address | 用户配置后采用的负载分担类型：按照源MAC地址和目的MAC地址进行负载分担（此字段的显示内容与用户的配置相关） |
| --- | --- |


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-1830420032.htm -->

irf domain命令用来配置IRF域编号。

undo irf domain命令用来恢复缺省情况。

【命令】

irf domain domain-id

undo irf domain

【缺省情况】

IRF的域编号为0。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

domain-id：IRF的域编号，取值范围为0～4294967295。

【使用指导】

为了适应各种组网应用，同一个网络里可以部署多个IRF。多个IRF之间使用不同的域编号以示区别。

如果LACP MAD、ARP MAD、或ND MAD组网的中间设备本身也是一个IRF系统，则必须配置该命令确保IRF和中间设备的IRF域编号不同，否则可能造成检测异常，甚至导致业务中断。

IRF中的所有成员设备都共用这个IRF域编号。在IRF设备上使用irf domain、mad enable、mad arp enable、mad nd enable命令均可修改全局IRF域编号，最新的配置生效。请按照网络规划来修改IRF域编号，不要随意修改。

【举例】

\# 配置IRF的域编号为10。

<Sysname> system-view

[Sysname] irf domain 10


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-2050990201.htm -->

irf-port global load-sharing mode命令用来配置全局IRF链路的负载分担模式。

undo irf-port global load-sharing mode命令用来恢复缺省情况。

【命令】

irf-port global load-sharing mode { destination-ip | destination-mac | source-ip | source-mac } *

undo irf-port global load-sharing mode

【缺省情况】

IRF链路通过报文类型来进行负载分担。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

destination-ip：表示按报文的目的IP地址进行负载分担。

destination-mac：表示按报文的目的MAC地址进行负载分担。

source-ip：表示按报文的源IP地址进行负载分担。

source-mac：表示按报文的源MAC地址进行负载分担。

【使用指导】

用户可以通过本命令配置全局的IRF链路负载分担模式，也可以通过irf-port load-sharing mode1.1.18 命令配置指定IRF端口的负载分担模式：

· 在系统视图的配置对所有IRF链路生效；

· 在IRF端口视图下的配置只对当前IRF端口下的IRF链路生效；

· IRF链路会优先采用端口下的配置。如果端口下没有配置，则采用全局配置。

多次执行本命令，最后一次执行的命令生效。

对于设备不支持的负载分担模式，系统将提示用户不支持。

【举例】

\# 配置全局按照报文目的MAC地址进行负载分担。

<Sysname> system-view

[Sysname] irf-port global load-sharing mode destination-mac

【相关命令】

· irf-port load-sharing mode


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-2071522514.htm -->

irf mac-address persistent命令用来配置IRF桥MAC的保留时间。

undo irf mac-address persistent命令用来配置IRF桥MAC不保留，立即变化。

【命令】

irf mac-address persistent { always | timer }

undo irf mac-address persistent

【缺省情况】

IRF桥MAC的保留时间为6分钟。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

always：配置IRF桥MAC永久保留。如果配置了MAC地址永久保留，则无论IRF桥MAC拥有者是否离开IRF，IRF桥MAC始终保持不变。

timer：配置IRF桥MAC的保留时间为6分钟。如果配置了桥MAC保留时间为6分钟，则当IRF桥MAC拥有者离开IRF时，IRF桥MAC在6分钟内不变化。如果IRF桥MAC拥有者在6分钟内重新又加入IRF，则IRF桥MAC不会变化。如果6分钟后IRF桥MAC拥有者没有回到IRF，则会使用IRF当前主设备的桥MAC作为IRF桥MAC。

【使用指导】

IRF桥MAC保留时间是指在桥MAC拥有者离开IRF后，IRF可以继续使用当前桥MAC的时间。

如果配置了MAC地址不保留，立即变化，当IRF桥MAC拥有者离开IRF时，系统立即会使用IRF中当前主设备的桥MAC做IRF桥MAC。

如果使用irf mac-address mac-address命令配置了IRF设备桥MAC地址，则IRF的桥MAC始终为irf mac-address mac-address命令配置的桥MAC地址，不受irf mac-address persistent命令影响。

当使用ARP MAD/ND MAD和MSTP组网时，需要将IRF配置为MAC地址立即改变，即配置undo irf mac-address persistent命令，同时请不要使用irf mac-address mac-address命令配置IRF的桥MAC为指定MAC地址，以避免流量中断。

当IRF设备上存在跨成员设备的聚合链路时，请不要使用undo irf mac-address persistent命令配置IRF的桥MAC立即变化，否则可能会导致流量中断。

缺省情况下，IRF的桥MAC为IRF中当前主设备的桥MAC。

如果两台物理设备的桥MAC相同，则它们不能合并为一个IRF。IRF的桥MAC不受此限制，只要成员设备自身桥MAC唯一即可。

【举例】

\# 配置IRF的桥MAC保留时间为永久保留。

<Sysname> system-view

[Sysname] irf mac-address persistent always


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-260581594.htm -->

mad bfd enable命令用来开启BFD MAD检测功能。

undo mad bfd enable用来关闭BFD MAD检测功能。

【命令】

mad bfd enable

undo mad bfd enable

【缺省情况】

BFD MAD检测功能处于关闭状态。

【视图】

三层接口视图

管理用以太网口视图

【缺省用户角色】

network-admin

【使用指导】

BFD MAD和ARP MAD、ND MAD冲突处理的原则不同，并且BFD MAD和生成树协议互斥，ARP MAD、ND MAD需要开启生成树协议，因此BFD MAD和ARP MAD、ND MAD无法同时配置。

使用VLAN接口进行BFD MAD检测时，请注意[表1-7](#_Ref429318068)所列配置注意事项。

表1-7 使用VLAN接口进行BFD MAD检测

| BFD MAD IP地址 | · 在用于BFD MAD检测的接口下必须使用mad ip address命令配置MAD IP地址，而不要配置其它IP地址（包括使用ip address命令配置的普通IP地址、VRRP虚拟IP地址等），以免影响MAD检测功能 · 为不同成员设备配置同一网段内的不同MAD IP地址 |
| --- | --- |

使用管理用以太网口进行BFD MAD检测时，请注意[表1-8](#_Ref429318112)所列配置注意事项。

表1-8 使用管理用以太网口进行BFD MAD检测

| MAD IP地址 | · 在管理用以太网口使用mad ip address命令配置MAD IP地址，请勿使用 ip address命令配置 · 为不同成员设备配置同一网段内的不同MAD IP地址 |
| --- | --- |

【举例】

\# 在VLAN接口3上启用BFD MAD检测功能。

<Sysname> system-view

[Sysname] interface vlan-interface 3

[Sysname-Vlan-interface3] mad bfd enable


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-28062350.htm -->

display irf命令用来显示IRF的相关信息。

【命令】

display irf

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【举例】

\# 显示IRF的相关信息。

<Sysname> display irf

MemberID Role Priority CPU-Mac Description

 1 Loading 1 00e0-fcbe-3102 F1Num001

 *+2 Master 1 00e0-fcb1-ade2 F1Num002

--------------------------------------------------------

 * indicates the device is the master.

 + indicates the device through which the user logs in.

 The Bridge MAC of the IRF is: 00e0-fc00-1000

 Auto upgrade: yes

 Mac persistent: always

 Domain ID: 30

表1-1 display irf命令显示信息描述表

| Domain ID | IRF的域编号 当网络中存在多个IRF时，用来唯一标识一个IRF |
| --- | --- |

【相关命令】

· display irf configuration

· display irf topology


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-792496914.htm -->

display mad命令用来显示MAD配置信息。

【命令】

display mad [ verbose ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

verbose：显示MAD详细配置信息。如果不指定该参数，则显示简要配置信息。

【举例】

\# 显示MAD简要配置信息。

<Sysname> display mad

MAD ARP enabled.

MAD ND enabled.

MAD LACP disabled.

MAD BFD disabled.

\# 显示MAD详细配置信息。

<Sysname> display mad verbose

Multi-active recovery state: No

Excluded ports(user-configured):

 Vlan-interface999

Excluded ports(system-configured):

 Ten-GigabitEthernet1/0/5

 Ten-GigabitEthernet1/0/6

 Ten-GigabitEthernet1/0/7

 Ten-GigabitEthernet1/0/8

 Ten-GigabitEthernet2/0/5

 Ten-GigabitEthernet2/0/6

 Ten-GigabitEthernet2/0/7

 Ten-GigabitEthernet2/0/8

MAD ARP enabled interface:

 Vlan-interface2

MAD ND enabled interface:

 Vlan-interface2

MAD LACP enabled interface: Bridge-Aggregation 1

 MAD status: Normal

 Member ID Port MAD status

 1 Ten-GigabitEthernet1/0/1 Normal

 2 Ten-GigabitEthernet2/0/1 Normal

MAD BFD enabled interface: VLAN-interface 3

 MAD status: Normal

 Member ID MAD IP address Neighbor MAD status

 1 192.168.1.1/24 2 Normal

 1 192.168.1.1/24 3 Normal

 2 192.168.1.2/24 1 Normal

 2 192.168.1.2/24 3 Normal

 3 192.168.1.3/24 1 Normal

 3 192.168.1.3/24 2 Normal

表1-6 display mad命令显示信息描述表

| Member ID MAD IP address Neighbor MAD status | BFD MAD详细信息： · Member ID：IRF中的成员设备编号 · MAD IP address：各成员设备对应的MAD IP地址 · Neighbor：邻居设备的成员编号 · MAD status：IRF设备成员到邻居成员的BFD MAD工作状态，Normal表示正常，Faulty表示不正常 |
| --- | --- |


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-862395492.htm -->

irf-port命令用来进入IRF端口视图。

undo irf-port用来取消IRF端口上的所有配置。

【命令】

irf-port member-id/irf-port-number

undo irf-port member-id/irf-port-number

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

member-id：表示设备在IRF中的成员编号。

irf-port-number表示IRF端口索引，取值为1时表示IRF-port1，为2时表示IRF-port2。

【使用指导】

在组建IRF前，必须进入IRF端口视图，并绑定IRF物理端口才能开启该IRF端口，从而进行IRF连接。

【举例】

\# 进入IRF端口2/1。

<Sysname> system-view

[Sysname] irf-port 2/1

[Sysname-irf-port2/1]

【相关命令】

· port group interface


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_-968689159.htm -->

display irf link命令用来显示IRF链路信息。

【命令】

display irf link

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【举例】

\# 显示IRF链路信息。

<Sysname> display irf link

Member 1

 IRF Port Interface Status

 1 disable --

 2 Ten-GigabitEthernet1/0/1 UP

 Ten-GigabitEthernet1/0/2 ADM

 Ten-GigabitEthernet1/0/3 DOWN

Member 2

 IRF Port Interface Status

 1 Ten-GigabitEthernet2/0/1 UP

 Ten-GigabitEthernet2/0/2 DOWN

 Ten-GigabitEthernet2/0/3 ADM

 2 disable --

表1-3 display irf link命令显示信息描述表

| Status | IRF端口的物理接口的链路状态 · UP：链路up · DOWN：链路down · ADM：用户在接口下执行了shutdown命令 · ABSENT：接口不存在，没有插入接口模块 |
| --- | --- |


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1038571938.htm -->

mad arp enable命令用来开启ARP MAD检测功能。

undo mad arp enable用来关闭ARP MAD检测功能。

【命令】

mad arp enable

undo mad arp enable

【缺省情况】

ARP MAD检测功能处于关闭状态。

【视图】

VLAN接口视图

管理用以太网口视图

【缺省用户角色】

network-admin

【使用指导】

VLAN 1不能用于MAD检测，因此，不能在VLAN接口1下开启ARP MAD检测功能。

ARP MAD、ND MAD和LACP MAD冲突处理的原则不同，请不要同时配置。

ARP MAD、ND MAD和BFD MAD冲突处理的原则不同，并且ARP MAD、ND MAD需要开启生成树协议，BFD MAD和生成树协议互斥，因此ARP MAD、ND MAD和BFD MAD无法同时配置。

在ARP MAD检测组网中，如果中间设备本身也是一个IRF系统，则必须通过配置确保其IRF域编号与被检测的IRF系统不同，否则可能造成检测异常，甚至导致业务中断。

为了防止IRF级联组网时，本IRF的MAD检测报文转发到邻居IRF中影响邻居IRF的MAD检测，执行mad arp enable命令时，系统会要求用户输入IRF域编号。如果继续使用当前编号，则直接按回车即可。

IRF域编号是一个全局变量，在IRF设备上使用irf domain、mad enable、mad arp enable、mad nd enable命令均可修改全局IRF域编号，最新的配置生效。

【举例】

\# 在VLAN接口3上启用ARP MAD检测功能。

<Sysname> system-view

[Sysname] interface vlan-interface 3

[Sysname-Vlan-interface3] mad arp enable

You need to assign a domain ID (range: 0-4294967295)

[Current domain is: 0]: 1

The assigned domain ID is: 1

【相关命令】

· irf domain


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1088514286.htm -->

irf mac-address命令用来配置IRF的桥MAC地址为指定值。

undo irf mac-address命令用来恢复缺省情况。

【命令】

irf mac-address mac-address

undo irf mac-address

【缺省情况】

IRF的桥MAC地址是Master设备的桥MAC地址。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

mac-address：IRF的桥MAC地址，形式为H-H-H，不支持组播MAC地址、全0、全F的MAC地址。在配置时，用户可以省去MAC地址中每段开头的“0”，例如输入“f-e2-1”即表示输入的MAC地址为“000f-00e2-0001”。

【使用指导】

当您需要使用新搭建的IRF设备整体替换网络中原有IRF设备时，可以将新搭建IRF的桥MAC配置为与待替换IRF设备一致，以减少替换工作引起的业务中断时间。

配置本命令后，IRF的桥MAC始终为本命令指定的桥MAC。未配置本命令时，IRF会选用某台成员设备的桥MAC作为IRF的桥MAC，具体请参见“1.1.12 irf mac-address persistent”。

配置IRF的桥MAC时，需要注意：

· 桥MAC变化可能导致流量短时间中断，请谨慎配置。

· 请确保配置的IRF的桥MAC地址在所处二层网络中唯一。

· 如果两台物理设备的桥MAC相同，则它们不能合并为一个IRF。IRF的桥MAC不受此限制，只要成员设备自身桥MAC唯一即可。

两个IRF合并后，IRF的桥MAC为竞选优胜的一方的桥MAC。

配置了桥MAC的IRF分裂后，分裂出的IRF的桥MAC都为配置的桥MAC。

【举例】

\# 配置IRF的桥MAC地址为c4ca-d9e0-8c3c。

<Sysname> system-view

[Sysname] irf mac-address c4ca-d9e0-8c3c


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1088638702.htm -->

mad ip address命令用来为成员设备配置MAD IP地址。

undo mad ip address命令用来删除成员设备的MAD IP地址。

【命令】

mad ip address ip-address { mask | mask-length } member member-id

undo mad ip address ip-address { mask | mask-length } member member-id

【缺省情况】

没有为成员设备配置MAD IP地址。

【视图】

三层接口视图

管理用以太网口视图

【缺省用户角色】

network-admin

【参数】

ip-address：接口的IP地址，为点分十进制格式。

mask：接口IP地址相应的子网掩码，为点分十进制格式。

mask-length：子网掩码长度，即掩码中连续“1”的个数，取值范围为0～32。

member member-id：表示成员在IRF中的成员编号。

【使用指导】

当使用BFD MAD检测时，IRF中的所有成员设备都需要配置MAD IP地址，这些IP地址与成员编号绑定，且必须为同一网段。只有主设备的MAD IP地址生效，从设备的MAD IP地址不生效。当IRF链路分裂时，IRF中的原从设备变为主设备，配置的MAD IP地址生效，BFD会话被激活，设备将认为在网络中检测到存在配置冲突的IRF。

在用于BFD MAD检测的接口不要配置其它IP地址（包括使用ip address命令配置的普通IP地址、VRRP虚拟IP地址等），以免影响MAD检测功能。

【举例】

\# 配置VLAN接口3在成员设备1上的MAD IP地址。

<Sysname> system-view

[Sysname] interface vlan-interface 3

[Sysname-Vlan-interface3] mad ip address 192.168.0.1 255.255.255.0 member 1

配置VLAN接口3在成员设备2上的MAD IP地址。

[Sysname-Vlan-interface3] mad ip address 192.168.0.2 255.255.255.0 member 2

【相关命令】

· mad bfd enable


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1268652973.htm -->

irf member renumber命令用来配置设备的成员编号。

undo irf member renumber命令用来取消成员编号的设置。

【命令】

irf member member-id renumber new-member-id

undo irf member member-id renumber

【缺省情况】

设备的成员编号是1。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

member-id：表示设备在IRF中的成员编号，取值范围为1~10。

new-member-id：表示修改后的成员编号，取值范围为1~10。

【使用指导】

在IRF中以设备编号标志设备，配置IRF端口和优先级也是根据设备编号来配置的，所以，修改设备成员编号可能导致设备配置发生变化或者丢失，请慎重处理。

当新加入的设备的编号和IRF中已有成员设备的编号相同时，设备不能加入IRF。此时，请使用该命令修改设备的成员编号后，重新加入IRF。

H3C建议您修改成员设备编号时勿配置两台成员设备编号互换。这样配置可能带来非预期的配置互换或数据丢失。例如配置成员设备2和3编号互换会引起对应接口下的配置也发生互换。

该配置需要重启member-id标识的设备才能生效。

undo irf member renumber命令只能取消本次运行过程中配置的成员编号。设备重启后，设备的成员编号就变为new-member-id，不能再取消，只能重新配置。

【举例】

\# 配置IRF中设备（原成员编号为1）的成员编号为2。

<Sysname> system-view

[Sysname] irf member 1 renumber 2

Renumbering the member ID may result in configuration change or loss. Continue?[Y/N]y

如果要取消以上配置，使设备的成员编号仍然是1，则可以执行以下命令：

[Sysname] undo irf member 1 renumber

Renumbering the member ID may result in configuration change or loss. Continue?[Y/N]y

如果配置irf member 1 renumber 2后，重启设备，则设备的成员编号会变为2。此时，不能使用undo irf member 1 renumber恢复到编号1，只能使用irf member 2 renumber 1重新配置。


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1465607822.htm -->

display irf topology命令用来查看IRF的拓扑信息。

【命令】

display irf topology

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【举例】

\# 显示IRF的拓扑信息。

<Sysname> display irf topology

 Topology Info

 -------------------------------------------------------------------------

 IRF-Port1 IRF-Port2

 MemberID Link neighbor Link neighbor Belong To

 1 DOWN --- UP 2 000f-cbb8-1a82

 2 UP 1 DIS --- 000f-cbb8-1a82

表1-4 display irf topology命令显示信息描述表

| Belong To | 所属IRF，用IRF中当前主设备的CPU MAC地址表示 |
| --- | --- |

【相关命令】

· display irf

· display irf configuration


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1542946933.htm -->

irf member priority命令用来配置IRF中成员设备的优先级。

undo irf member priority命令用来恢复缺省情况。

【命令】

irf member member-id priority priority

undo irf member member-id priority

【缺省情况】

设备的成员优先级均为1。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

member-id：表示设备在IRF中的成员编号，取值范围为1~10。

priority：表示优先级，取值范围为1～32。优先级值越大表示优先级越高，优先级高的设备竞选时成为主设备的可能性越大。

【使用指导】

本命令的配置会影响成员设备在下一次选举中的角色，但不会触发选举。

【举例】

\# 配置IRF中成员编号为2的设备的优先级为32。

<Sysname> system-view

[Sysname] irf member 2 priority 32


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1703765666.htm -->

display irf configuration命令用来显示IRF中所有成员设备的IRF配置。

【命令】

display irf configuration

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【举例】

\# 显示IRF中所有成员设备的IRF配置。

<Sysname> display irf configuration

 MemberID NewID IRF-Port1 IRF-Port2

 2 2 Ten-GigabitEthernet2/0/5 Ten-GigabitEthernet2/0/6

 5 5 Ten-GigabitEthernet5/0/5 Ten-GigabitEthernet5/0/6

 Ten-GigabitEthernet5/0/7

 Ten-GigabitEthernet5/0/8

 10 10 Ten-GigabitEthernet10/0/5 Ten-GigabitEthernet10/0/6

 Ten-GigabitEthernet10/0/7

 Ten-GigabitEthernet10/0/8

表1-2 display irf configuration命令显示信息描述表

| IRF-Port2 | IRF端口2的配置 · 如果显示信息中包含多个物理端口，则表示该IRF端口由多个IRF物理端口聚合而成 · 如果显示为disable，则表示该IRF端口还没有和IRF物理端口绑定 |
| --- | --- |

【相关命令】

· display irf

· display irf topology


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1836066622.htm -->

irf-port load-sharing mode命令用来配置端口下IRF链路的负载分担模式。

undo irf-port load-sharing mode命令用来恢复缺省情况。

【命令】

irf-port load-sharing mode { destination-ip | destination-mac | source-ip | source-mac } *

undo irf-port load-sharing mode

【缺省情况】

IRF端口使用全局IRF链路负载分担模式。

【视图】

IRF端口视图

【缺省用户角色】

network-admin

【参数】

destination-ip：表示按报文的目的IP地址进行负载分担。

destination-mac：表示按报文的目的MAC地址进行负载分担。

source-ip：表示按报文的源IP地址进行负载分担。

source-mac：表示按报文的源MAC地址进行负载分担。

【使用指导】

在配置负载分担模式前，请先将IRF端口和IRF物理端口绑定。否则，负载分担模式将配置失败。用户可以通过本命令配置指定IRF端口的负载分担模式，也可以通过irf-port global load-sharing mode命令配置全局的IRF链路负载分担模式：

· 在系统视图的配置对所有IRF链路生效；

· 在IRF端口视图下的配置只对当前IRF端口下的IRF链路生效；

· IRF链路会优先采用端口下的配置。如果端口下没有配置，则采用全局配置。

多次执行本命令，最后一次执行的命令生效。

对于设备不支持的负载分担模式，系统将提示用户不支持。

【举例】

\# 配置按报文目的MAC地址实现IRF端口1/1下IRF链路的负载分担模式。

<Sysname> system-view

[Sysname] irf-port 1/1

[Sysname-irf-port1/1] irf-port load-sharing mode destination-mac

【相关命令】

· irf-port global load-sharing mode


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_1944741454.htm -->

mad restore命令用来将设备从Recovery状态恢复到正常状态。

【命令】

mad restore

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

当IRF链路故障会导致多Active冲突，原IRF分裂为多个IRF，为了防止网络中配置冲突，IRF系统会通过多Active检测机制，让其中一个IRF继续正常工作，其它IRF的状态修改为Recovery（处于该状态的IRF不能处理业务报文）。如果继续正常工作的IRF也发生故障不能工作，此时可以通过本命令将处于Recovery状态的IRF恢复到正常工作状态接替原IRF工作，以便保证业务尽量少受影响。

【举例】

\# 将IRF从Recovery状态恢复到正常状态。

<Sysname> system-view

[Sysname] mad restore

 This command will restore the device from multi-active conflict state. Continue? [Y/N]:Y

Restoring from multi-active conflict state, please wait...


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_2016815825.htm -->

irf member description命令用来配置IRF中成员设备的描述信息。

undo irf member description命令用来恢复缺省情况。

【命令】

irf member member-id description text

undo irf member member-id description

【缺省情况】

未配置成员设备的描述信息。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

member-id：表示设备在IRF中的成员编号。

text：设备的描述信息，为1～127个字符的字符串。

【举例】

\# 配置成员设备1的描述信息为F1Num001。

<Sysname> system-view

[Sysname] irf member 1 description F1Num001


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_391484221.htm -->

irf link-delay命令用来配置IRF链路中断的延迟上报时间。

undo irf link-delay命令用来恢复缺省情况。

【命令】

irf link-delay interval

undo irf link-delay

【缺省情况】

IRF链路中断的延迟上报时间为4000毫秒，即4秒。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

interval：表示IRF链路中断的延迟上报时间，取值范围为0～10000，单位为毫秒。取值为0时，表示不延迟。

【使用指导】

在IRF环境中使用CFD或BFD功能时，请保证IRF链路down延迟上报时间小于CFD或BFD的超时时间，关于CFD和BFD功能的介绍，请参见“可靠性配置指导”中的“CFD”和“BFD”。

【举例】

\# 配置IRF链路中断的延迟上报时间为300毫秒。

<Sysname> system-view

[Sysname] irf link-delay 300


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_719004157.htm -->

mad exclude interface命令用来配置保留接口。

undo mad exclude interface命令用来将接口配置为非保留接口。

【命令】

mad exclude interface interface-type interface-number

undo mad exclude interface interface-type interface-number

【缺省情况】

仅IRF物理端口是保留接口。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

interface-type interface-number：表示接口类型和接口编号。

【使用指导】

设备进入Recovery状态时会自动关闭本设备上所有的业务接口。如果希望Recovery状态IRF上有特殊用途的接口（比如Telnet登录接口）保持UP状态，可以将其配置为保留接口。建议您仅将Telnet登录接口配置为保留接口。

请勿将用于MAD检测的聚合接口及其成员接口、VLAN接口及该VLAN中的二层以太网接口、管理用以太网口配置为保留接口。

当分裂的IRF恢复时，处于Recovery状态的设备重启后重新加入IRF，被MAD关闭的接口会自动恢复到正常状态。

在MAD故障未修复，接口没有自动恢复时，如果需要让Recovery状态IRF中的成员设备及其接口恢复到正常状态（原因可能是Active状态的IRF出现故障），可以在Recovery状态IRF上执行mad restore命令。

【举例】

\# 配置Ten-GigabitEthernet1/0/1为保留接口，即当设备进入Recovery状态时，该接口不会被关闭。

<Sysname> system-view

[Sysname] mad exclude interface ten-gigabitethernet 1/0/1

【相关命令】

· mad restore


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_866087449.htm -->

irf-port-configuration active命令用于来激活设备上所有IRF端口的配置。

【命令】

irf-port-configuration active

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

IRF物理线缆连接好，并将IRF物理端口添加到IRF端口后，必须通过该命令手工激活IRF端口的配置才能形成IRF。

系统启动，通过配置文件将IRF物理端口加入IRF端口，或者IRF形成后再加入新的IRF物理端口时，IRF端口下的配置会自动激活不再需要使用该命令来激活。

【举例】

\# 在IRF端口1/2状态为DIS的情况下，激活IRF端口的配置。

· IRF端口状态为DIS表示IRF端口还没有与任何IRF物理端口绑定，所以，先配置绑定关系。绑定前需要先将IRF物理端口关闭，绑定后再将IRF物理端口激活。

<Sysname> system-view

[Sysname] interface ten-gigabitEthernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] shutdown

[Sysname-Ten-GigabitEthernet1/0/1] quit

[Sysname] irf-port 1/2

[Sysname-irf-port1/2] port group interface Ten-GigabitEthernet 1/0/1

You must perform the following tasks for a successful IRF setup:

Save the configuration after completing IRF configuration.

Execute the "irf-port-configuration active" command to activate the IRF ports.

[Sysname-irf-port1/2] quit

[Sysname] interface ten-gigabitEthernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] undo shutdown

[Sysname-Ten-GigabitEthernet1/0/1] quit

· 将当前配置保存到下次启动配置文件，以便IRF端口的配置在设备重启后能继续生效。

[Sysname] save

The current configuration will be written to the device. Are you sure? [Y/N]:y

Please input the file name(*.cfg)[flash:/startup.cfg]

(To leave the existing filename unchanged, press the enter key):

flash:/aa.cfg exists, overwrite? [Y/N]:y

 Validating file. Please wait............................

 Saved the current configuration to mainboard device successfully.

· 激活IRF端口的配置。

[Sysname] irf-port-configuration active


---

<!-- 02-IRF命令参考/html/-1496773680_-1710790416_1773461886_912742912.htm -->

port group interface命令用来绑定设备的IRF端口和IRF物理端口，在IRF端口上第一次绑定IRF物理端口的同时相当于开启了IRF端口的IRF功能。

undo port group interface命令用来取消设备的IRF端口和IRF物理端口的绑定关系。

【命令】

port group interface interface-type interface-number

undo port group interface interface-name

【缺省情况】

IRF端口创建后未与任何物理端口绑定。

【视图】

IRF端口视图

【缺省用户角色】

network-admin

【参数】

interface-type interface-number：表示IRF物理端口的类型和编号。

interface-name：IRF物理端口的名称，格式为interface-type+interface-number，interface-type与interface-number之间没有空格。

【使用指导】

多次执行该命令可以将同一IRF端口与多个IRF物理端口绑定，本系列交换机最多可以将8个IRF物理端口与一个IRF端口进行绑定。

需要先使用shutdown命令关闭相应的物理端口，才能将IRF端口与物理端口绑定或解绑定。在绑定或解绑定的操作完成后，需要执行undo shutdown命令开启物理端口。

配置本命令后，即便热插拔接口模块扩展卡导致绑定的IRF物理端口不存在了，但绑定关系仍然存在，使用undo port group interface命令可以取消绑定关系。

更多配置要求，请参见“IRF配置指导”中的“IRF”。

【举例】

\# 将成员设备1的IRF物理端口Ten-GigabitEthernet1/0/1和IRF端口IRF-port1绑定。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] shutdown

[Sysname-Ten-GigabitEthernet1/0/1] quit

[Sysname] irf-port 1/1

[Sysname-irf-port1/1] port group interface ten-gigabitethernet 1/0/1

[Sysname-irf-port1/1] quit

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] undo shutdown

【相关命令】

· irf-port


---

<!-- 02-IRF命令参考/html/00-前言.htm -->

前 言

本命令参考主要介绍了在组建基于IRF技术的虚拟化设备的过程中所需要使用的命令，包括配置IRF端口绑定、配置成员设备的编号和优先级，以及IRF链路的检测和维护过程中所使用的命令。

前言部分包含如下内容：

· [读者对象](#_Ref259627501)

· [本书约定](#_Ref259627585)

· [资料获取方式](#_Ref259634437)

· [技术支持](#_Ref259627591)

· [资料意见反馈](#_Ref259627594)

## 读者对象

本手册主要适用于如下工程师：

· 网络规划人员

· 现场技术支持与维护人员

· 负责网络配置和维护的网络管理员

## 本书约定

#### 1. 命令行格式约定

| # | 由“#”号开始的行表示为注释行。 |
| --- | --- |

#### 2. 图形界面格式约定

| / | 多级菜单用“/”隔开。如[文件/新建/文件夹]多级菜单表示[文件]菜单下的[新建]子菜单下的[文件夹]菜单项。 |
| --- | --- |

#### 3. 各类标志

本书还采用各种醒目标志来表示在操作过程中应该特别注意的地方，这些标志的意义如下：

| | 配置、操作、或使用设备的技巧、小窍门。 |
| --- | --- |

#### 4. 图标约定

本书使用的图标及其含义如下：

| | 该图标及其相关描述文字代表防火墙插卡、负载均衡插卡、NetStream插卡、SSL VPN插卡、IPS插卡、ACG插卡等安全插卡。 |
| --- | --- |

#### 5. 示例约定

由于设备型号不同、配置不同、版本升级等原因，可能造成本手册中的内容与用户使用的设备显示信息不一致。实际使用中请以设备显示的内容为准。

本手册中出现的端口编号仅作示例，并不代表设备上实际具有此编号的端口，实际使用中请以设备上存在的端口编号为准。

## 资料获取方式

您可以通过H3C网站（[www.h3c.com](http://www.h3c.com/)）获取最新的产品资料：

· 获取安装类、配置类或维护类等产品资料

[http://www.h3c.com/cn/Technical_Documents](http://www.h3c.com/cn/Technical_Documents)

· 获取版本说明书等与软件版本配套的资料

[http://www.h3c.com/cn/Software_Download](http://www.h3c.com/cn/Software_Download)

## 技术支持

用户支持邮箱：service@h3c.com

技术支持热线电话：400-810-0504（手机、固话均可拨打）

网址：[http://www.h3c.com](http://www.h3c.com/)

## 资料意见反馈

如果您在使用过程中发现产品资料的任何问题，可以通过以下方式反馈：

E-mail：info@h3c.com

感谢您的反馈，让我们做得更好！
