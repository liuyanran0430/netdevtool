# 07-MCE命令参考

<!-- 07-MCE命令参考/html/-2032530497_-1666862242.htm -->

## 2 IPv6 MCE

本章只介绍IPv6 MCE的相关命令，IPv4 MCE和IPv6 MCE的公共命令请参见“MCE命令参考”中的“MCE”。


---

<!-- 07-MCE命令参考/html/-2032530497_-1666862242_-888123562_-394217118.htm -->

vpn-instance-capability simple命令用来关闭OSPFv3的路由环路检测功能。

undo vpn-instance-capability命令用来开启OSPFv3的路由环路检测功能。

【命令】

vpn-instance-capability simple

undo vpn-instance-capability

【缺省情况】

OSPFv3的路由环路检测功能处于开启状态。

【视图】

OSPFv3视图

【缺省用户角色】

network-admin

【使用指导】

MCE组网环境中，需要在MCE设备上关闭OSPFv3的路由环路检测功能。否则，MCE设备不会接收PE设备发送过来的OSPFv3路由，导致路由丢失。

该命令只能在OSPFv3多实例进程下执行。

【举例】

\# 关闭OSPFv3多实例进程100的路由环路检测功能。

<Sysname> system-view

[Sysname] ospfv3 100 vpn-instance vpn1

[Sysname-ospfv3-100] vpn-instance-capability simple


---

<!-- 07-MCE命令参考/html/-2032530497_-1666862242_-888123562_-890474854.htm -->

address-family ipv6命令用来进入VPN实例IPv6 VPN视图。

undo address-family ipv6命令用来删除VPN实例IPv6 VPN视图下的所有配置。

【命令】

address-family ipv6

undo address-family ipv6

【视图】

VPN实例视图

【缺省用户角色】

network-admin

【使用指导】

在VPN实例IPv6 VPN视图下可以配置IPv6 VPN的参数，如IPv6 VPN应用的出方向路由策略、入方向路由策略等。

【举例】

\# 进入VPN实例IPv6 VPN视图。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] address-family ipv6

[Sysname-vpn-ipv6-vpn1]

【相关命令】

· address-family ipv4 (VPN instance view)


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_-2041219059.htm -->

vpn-instance-capability simple命令用来关闭OSPF实例的路由环路检测功能。

undo vpn-instance-capability命令用来开启OSPF实例的路由环路检测功能。

【命令】

vpn-instance-capability simple

undo vpn-instance-capability

【缺省情况】

OSPF实例的路由环路检测功能处于开启状态。

【视图】

OSPF视图

【缺省用户角色】

network-admin

【使用指导】

MCE组网环境中，需要在MCE设备上关闭OSPF实例的路由环路检测功能。否则，MCE不会接收PE发送过来的OSPF路由，导致路由丢失。

只有OSPF进程属于某个VPN时，才能在该进程对应的OSPF视图下成功执行本命令。

【举例】

\# 关闭OSPF实例的路由环路检测功能。

<Sysname> system-view

[Sysname] ospf 100 vpn-instance vpna

[Sysname-ospf-100] vpn-instance-capability simple


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_-2098066824.htm -->

display ip vpn-instance命令用来显示VPN实例的信息。

【命令】

display ip vpn-instance [ instance-name vpn-instance-name ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance-name vpn-instance-name：显示指定VPN实例的详细信息。vpn-instance-name表示VPN实例名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示创建的所有VPN实例的简要信息。

【举例】

\# 显示所有VPN实例的简要信息。

<Sysname> display ip vpn-instance

 Total VPN-Instances configured: 1

 VPN-Instance Name RD Create time

 abc 1:1 2011/05/18 10:48:17

表1-1 display ip vpn-instance命令显示信息描述表

| Create time | VPN实例创建的时间 |
| --- | --- |

\# 显示名为vpn1的VPN实例的详细信息。

<Sysname> display ip vpn-instance instance-name vpn1

 VPN-Instance Name and Index: vpn1, 2

 Route Distinguisher: 100:1

 VPN ID: 1:1

 Description: vpn1

 Interfaces: Vlan-interface2

 Address-family IPv4:

 Export VPN Targets:

 2:2

 Import VPN Targets:

 3:3

 Export Route Policy: outpolicy

 Import Route Policy: inpolicy

 Tunnel Policy: tunnel1

 Maximum Routes Limit: 500

 Threshold Value(%): 50

 Address-family IPv6:

 Export VPN Targets:

 2:2

 Import VPN Targets:

 3:3

 Export Route Policy: outpolicy

 Import Route Policy: inpolicy

 Tunnel Policy: tunnel1

 Maximum Routes Limit:500

 Threshold Value(%): 50

表1-2 display ip vpn-instance instance-name命令显示信息描述表

| Threshold Value(%) | 激活路由条数的告警门限值 |
| --- | --- |


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_-23239575.htm -->

address-family ipv4命令用来进入VPN实例IPv4 VPN视图。

undo address-family ipv4命令用来删除VPN实例IPv4 VPN视图下的所有配置。

【命令】

address-family ipv4

undo address-family ipv4

【视图】

VPN实例视图

【缺省用户角色】

network-admin

【使用指导】

在VPN实例IPv4 VPN视图下可以配置IPv4 VPN的参数，如IPv4 VPN应用的出方向路由策略、入方向路由策略等。

【举例】

\# 进入VPN实例IPv4 VPN视图。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] address-family ipv4

[Sysname-vpn-ipv4-vpn1]

【相关命令】

· address-family ipv6 (VPN instance view)


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_-367507604.htm -->

ip binding vpn-instance命令用来配置接口与指定VPN实例关联。

undo ip binding vpn-instance命令用来恢复缺省情况。

【命令】

ip binding vpn-instance vpn-instance-name

undo ip binding vpn-instance

【缺省情况】

接口未关联VPN实例，接口属于公网。

【视图】

接口视图

【缺省用户角色】

network-admin

【参数】

vpn-instance-name：接口关联的VPN实例名称，为1～31个字符的字符串，区分大小写。

【使用指导】

本命令用于在PE设备上将连接CE的接口与该CE所属的VPN实例关联。

配置或取消接口与VPN实例关联后，该接口上的IP地址、路由协议等配置将被删除。

接口关联的VPN实例，必须已经通过系统视图下的ip vpn-instance命令创建。

不能通过重复执行本命令修改接口关联的VPN实例。如需修改接口关联的VPN实例，请先通过undo ip binding vpn-instance命令取消关联的VPN实例后，再执行ip binding vpn-instance命令关联新的VPN实例。

【举例】

\# 将接口Vlan-interface2与名为vpn1的VPN实例关联。

<Sysname> system-view

[Sysname] interface vlan-interface 2

[Sysname-Vlan-interface2] ip binding vpn-instance vpn1

【相关命令】

· ip vpn-instance (System view)


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_-87613227.htm -->

ip vpn-instance命令用来创建VPN实例，并进入VPN实例视图。如果指定的VPN实例已经存在，则直接进入VPN实例视图。

undo ip vpn-instance命令用来删除指定的VPN实例。

【命令】

ip vpn-instance vpn-instance-name

undo ip vpn-instance vpn-instance-name

【缺省情况】

不存在VPN实例。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

vpn-instance-name：VPN实例的名称，为1～31个字符的字符串，区分大小写。

【举例】

\# 创建一个名为vpn1的VPN实例，并进入VPN实例视图。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1]

【相关命令】

· route-distinguisher


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_-894739236.htm -->

vpn-id命令用来配置VPN实例的ID。

undo vpn-id命令用来恢复缺省情况。

【命令】

vpn-id vpn-id

undo vpn-id

【缺省情况】

未配置VPN实例的ID。

【视图】

VPN实例视图

【缺省用户角色】

network-admin

【参数】

vpn-id：VPN实例的ID，取值形式为OUI:Index。其中，OUI（Organizationally Unique Identifier，全球统一标识符）的取值范围为十六进制数0～FFFFFF；Index的取值范围为十六进制数0～FFFFFFFF。

【使用指导】

VPN ID是VPN实例的唯一标识，不同VPN实例的VPN ID不能相同。

VPN ID的取值不能为0:0。

【举例】

\# 配置VPN实例vpn1的ID为20:1。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] vpn-id 20:1

【相关命令】

· display ip vpn-instance


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_1436818129.htm -->

vpn-target命令用来配置VPN实例的Route Target。

undo vpn-target命令用来删除VPN实例的Route Target。

【命令】

vpn-target vpn-target&<1-8> [ both | export-extcommunity | import-extcommunity ]

undo vpn-target { all | vpn-target&<1-8> [ both | export-extcommunity | import-extcommunity ] }

【缺省情况】

未配置指定VPN实例的Route Target。

【视图】

VPN实例视图

VPN实例IPv4 VPN视图

VPN实例IPv6 VPN视图

【缺省用户角色】

network-admin

【参数】

vpn-target&<1-8>：指定Route Target值。vpn-target为3～21个字符的字符串，取值为AS-number:nn或IP-address:nn。&<1-8>表示前面的参数最多可以输入8次。

Route Target有三种格式：

· 16位自治系统号:32位用户自定义数，例如：101:3。

· 32位IP地址:16位用户自定义数，例如：192.168.122.15:1。

· 32位自治系统号：16位用户自定义数字，其中的自治系统号最小值为65536。例如：65536:1。

both：指定配置的Route Target值同时作为Import Target和Export Target。如果未指定both、export-extcommunity和import-extcommunity中的任何一个参数时，缺省值为both。

export-extcommunity：指定配置的Route Target值为Export Target。

import-extcommunity：指定配置的Route Target值为Import Target。

all：所有Route Target值。

【使用指导】

Route Target用来控制VPN路由的发布。PE在发布的VPN路由中添加Route Target扩展团体属性，该属性的值为配置的Export Target。对端PE接收到VPN路由后，将路由中携带的Route Target属性与本地配置的VPN实例的Import Target进行比较，如果二者中存在相同的值，则将该路由学习到该VPN实例的路由表中。

VPN实例视图下的配置，既可以用于IPv4 VPN，也可以用于IPv6 VPN；VPN实例IPv4 VPN视图下的配置只能用于IPv4 VPN；VPN实例IPv6 VPN视图下的配置只能用于IPv6 VPN。

VPN实例IPv4 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv4 VPN视图和VPN实例视图下进行了配置，则IPv4 VPN采用VPN实例IPv4 VPN视图下的配置。

VPN实例IPv6 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv6 VPN视图和VPN实例视图下进行了配置，则IPv6 VPN采用VPN实例IPv6 VPN视图下的配置。

【举例】

\# 为名为vpn1的VPN实例配置Route Target。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] vpn-target 3:3 export-extcommunity

[Sysname-vpn-instance-vpn1] vpn-target 4:4 import-extcommunity

[Sysname-vpn-instance-vpn1] vpn-target 5:5 both


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_1811888544.htm -->

import route-policy命令用来配置VPN实例应用入方向路由策略。

undo import route-policy命令用来恢复缺省情况。

【命令】

import route-policy route-policy

undo import route-policy

【缺省情况】

VPN实例未应用入方向路由策略。如果接收到的路由携带的Route Target属性中存在与本地配置的Import Target相同的值，则接收该路由。

【视图】

VPN实例视图

VPN实例IPv4 VPN视图

VPN实例IPv6 VPN视图

【缺省用户角色】

network-admin

【参数】

route-policy：VPN实例的入方向路由策略名，为1～63个字符的字符串，区分大小写。

【使用指导】

如果在设备上通过本命令指定了VPN实例应用的入方向路由策略，则该VPN实例在接收其他VPN实例的路由后，将利用指定的路由策略对接收的路由进行过滤、改变接收路由的属性等。使用本命令可以更加精确、灵活地控制VPN实例之间路由的接收。

多次执行本命令，最后一次执行的命令生效。

VPN实例视图下的配置，既可以用于IPv4 VPN，也可以用于IPv6 VPN；VPN实例IPv4 VPN视图下的配置只能用于IPv4 VPN；VPN实例IPv6 VPN视图下的配置只能用于IPv6 VPN。

VPN实例IPv4 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv4 VPN视图和VPN实例视图下进行了配置，则IPv4 VPN采用VPN实例IPv4 VPN视图下的配置。

VPN实例IPv6 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv6 VPN视图和VPN实例视图下进行了配置，则IPv6 VPN采用VPN实例IPv6 VPN视图下的配置。

【举例】

\# 对名为vpn1的VPN实例应用入方向路由策略poly-1。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] import route-policy poly-1

【相关命令】

· export route-policy

· route-policy（三层技术-IP路由命令参考/路由策略）


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_2681861.htm -->

routing-table limit命令用来限制VPN实例支持的最多激活路由前缀数。

undo routing-table limit命令用来恢复缺省情况。

【命令】

routing-table limit number { warn-threshold | simply-alert }

undo routing-table limit

【缺省情况】

未限制VPN实例支持的最多激活路由前缀数。

【视图】

VPN实例视图

VPN实例IPv4 VPN视图

VPN实例IPv6 VPN视图

【缺省用户角色】

network-admin

【参数】

number：指定一个VPN实例最多可以支持的激活路由前缀数。在VPN实例视图下取值范围为1～8192，在VPN实例IPv4 VPN视图下的取值范围为1～16384；在VPN实例IPv6 VPN视图下的取值范围为1～8192。

warn-threshold：告警门限值，取值范围为1～100，单位为百分比。当（VPN实例中的激活路由前缀数/最多支持激活路由前缀数×100）达到告警门限值时，产生一条日志信息，但仍然允许激活路由前缀。当VPN实例中的激活路由前缀数达到最多支持激活路由前缀数目时，不再激活新的路由前缀。

simply-alert：指定当VPN实例的激活路由前缀数超过最多支持的激活路由前缀数目时，可以继续激活新的路由前缀，但会产生一条日志信息。

【使用指导】

通过本命令可以避免PE路由器引入太多的VPN激活路由前缀。

VPN实例视图下的配置，既可以用于IPv4 VPN，也可以用于IPv6 VPN；VPN实例IPv4 VPN视图下的配置只能用于IPv4 VPN；VPN实例IPv6 VPN视图下的配置只能用于IPv6 VPN。

VPN实例IPv4 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv4 VPN视图和VPN实例视图下进行了配置，则IPv4 VPN采用VPN实例IPv4 VPN视图下的配置。

VPN实例IPv6 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv6 VPN视图和VPN实例视图下进行了配置，则IPv6 VPN采用VPN实例IPv6 VPN视图下的配置。

【举例】

\# 限制名为vpn1的VPN实例最多可支持1000条激活路由前缀，并且当激活路由前缀数超过最多支持激活路由前缀数时，可以继续激活新的路由前缀，但是会产生一条日志信息。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] route-distinguisher 100:1

[Sysname-vpn-instance-vpn1] routing-table limit 1000 simply-alert


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_39293624.htm -->

route-distinguisher命令用来配置VPN实例的RD（Route Distinguisher，路由标识）。

undo route-distinguisher命令用来恢复缺省情况。

【命令】

route-distinguisher route-distinguisher

undo route-distinguisher

【缺省情况】

未配置VPN实例的RD。

【视图】

VPN实例视图

【缺省用户角色】

network-admin

【参数】

route-distinguisher：路由标识符，为3～21个字符的字符串。路由标识符有三种格式：

· 16位自治系统号:32位用户自定义数，例如：101:3。

· 32位IP地址:16位用户自定义数，例如：192.168.122.15:1。

· 32位自治系统号：16位用户自定义数字，其中的自治系统号最小值为65536。例如：65536:1。

【使用指导】

RD用于解决不同VPN之间地址空间重叠的问题。将RD添加到一个IPv4前缀之前，就可以使之成为全局唯一的VPN-IPv4地址前缀。

为了保证VPN-IPv4地址全球唯一，建议不要将自治系统号/IP地址设置为私有AS号/私有IP地址。

不能通过重复执行route-distinguisher命令修改VPN实例的RD值。如需修改VPN实例的RD值，请先通过undo route-distinguisher命令删除VPN实例的RD值，再执行route-distinguisher命令配置新的RD值。

【举例】

\# 配置VPN实例vpn1的RD为22:1。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] route-distinguisher 22:1


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_4239542.htm -->

description命令用来配置VPN实例的描述信息。

undo description命令用来恢复缺省情况。

【命令】

description text

undo description

【缺省情况】

未配置VPN实例的描述信息。

【视图】

VPN实例视图

【缺省用户角色】

network-admin

【参数】

text：VPN实例的描述信息，为1～79个字符的字符串，区分大小写。

【举例】

\# 配置名为vpn1的VPN实例的描述信息为“This is vpn1”。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] description This is vpn1


---

<!-- 07-MCE命令参考/html/-2032530497_-487572645_95409609_976403376.htm -->

export route-policy命令用来配置VPN实例应用出方向路由策略。

undo export route-policy命令用来恢复缺省情况。

【命令】

export route-policy route-policy

undo export route-policy

【缺省情况】

VPN实例未应用出方向路由策略，不对发布的路由进行过滤。

【视图】

VPN实例视图

VPN实例IPv4 VPN视图

VPN实例IPv6 VPN视图

【缺省用户角色】

network-admin

【参数】

route-policy：VPN实例的出方向路由策略名，为1～63个字符的字符串，区分大小写。

【使用指导】

如果在设备上通过本命令指定了VPN实例应用的出方向路由策略，则该VPN实例在向其他VPN实例发布路由时，将利用指定的路由策略对发布的路由进行过滤、改变发布路由的属性等。使用本命令可以更加精确、灵活地控制VPN实例之间路由的发布。

多次执行本命令，最后一次执行的命令生效。

VPN实例视图下的配置，既可以用于IPv4 VPN，也可以用于IPv6 VPN；VPN实例IPv4 VPN视图下的配置只能用于IPv4 VPN；VPN实例IPv6 VPN视图下的配置只能用于IPv6 VPN。

VPN实例IPv4 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv4 VPN视图和VPN实例视图下进行了配置，则IPv4 VPN采用VPN实例IPv4 VPN视图下的配置。

VPN实例IPv6 VPN视图下的配置优先级高于VPN实例视图下的配置，即如果同时在VPN实例IPv6 VPN视图和VPN实例视图下进行了配置，则IPv6 VPN采用VPN实例IPv6 VPN视图下的配置。

【举例】

\# 对名为vpn1的VPN实例应用出方向路由策略poly-1。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] export route-policy poly-1

【相关命令】

· import route-policy

· route-policy（三层技术-IP路由命令参考/路由策略）


---

<!-- 07-MCE命令参考/html/00-前言.htm -->

前 言

本命令参考主要介绍了S6800系列交换机配置MCE功能所使用的相关命令。

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
