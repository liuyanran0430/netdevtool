# 13-VXLAN命令参考

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1409308565.htm -->

selective-flooding mac-addres命令用来配置VSI选择性泛洪的MAC地址。

undo selective-flooding mac-addres命令用来删除VSI的选择性泛洪MAC地址。

【命令】

selective-flooding mac-addres mac-addres

undo selective-flooding mac-addres mac-addres

【缺省情况】

不存在VSI选择性泛洪MAC地址。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

mac-address：选择性泛洪的MAC地址。该MAC地址不能为全F。

【使用指导】

通过flooding disable命令关闭VSI的泛洪功能后，为了将某些单播或组播MAC地址的数据帧泛洪到远端站点以保证某些业务的流量在站点间互通，可以配置选择性泛洪的MAC地址。当数据帧的目的MAC地址匹配选择性泛洪的MAC地址时，该数据帧可以泛洪到远端站点。

【举例】

\# 在VSI vsi1下配置选择性泛洪的MAC地址为000f-e201-0101。

<Sysname> system-view

[Sysname] vsi vsi1

[Sysname-vsi-vsi1] selective-flooding mac-address 000f-e201-0101

【相关命令】

· flooding disable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1536807950.htm -->

tunnel global source-address命令用来配置VXLAN隧道的全局源地址。

undo tunnel global source-address命令用来恢复缺省情况。

【命令】

tunnel global source-address ip-address

undo tunnel global source-address

【缺省情况】

未配置VXLAN隧道的全局源地址。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

ip-address：隧道的全局源IP地址。

【使用指导】

目前仅VXLAN隧道支持全局源地址，其它类型的隧道不支持全局源地址。

如果隧道下未配置源地址或源接口，则隧道会使用全局源地址作为隧道的源地址。

采用OVSDB对VTEP设备进行部署和控制时，用户不能在VXLAN隧道的Tunnel接口下手工指定源地址，只能通过本命令指定全局源地址，否则会影响控制器对VTEP设备的管理。

【举例】

\# 配置VXLAN隧道的全局源地址为1.1.1.1。

<Sysname> system-view

[Sysname] tunnel global source-address 1.1.1.1


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1565189635.htm -->

arp suppression enable命令用来开启ARP泛洪抑制功能。

undo arp suppression enable命令用来关闭ARP泛洪抑制功能。

【命令】

arp suppression enable

undo arp suppression enable

【缺省情况】

ARP泛洪抑制功能处于关闭状态。

【视图】

VSI视图

【缺省用户角色】

network-admin

【使用指导】

为了避免广播发送的ARP请求报文过多占用核心网络带宽，VTEP从本地站点、VXLAN隧道接收到ARP请求和ARP应答报文后，根据该报文在本地建立ARP泛洪抑制表项。后续当VTEP收到本站点内虚拟机请求其它虚拟机MAC地址的ARP请求时，优先根据ARP泛洪抑制表项进行代答。如果没有对应的表项，则将ARP请求泛洪到核心网。ARP泛洪抑制功能可以大大减少ARP泛洪的次数。

【举例】

\# 在VSI vsi1下开启ARP泛洪抑制功能。

<Sysname> system-view

[Sysname] vsi vsi1

[Sysname-vsi-vsi1] arp suppression enable

【相关命令】

· display arp suppression vsi

· reset arp suppression vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1678527872.htm -->

reset l2vpn statistics vsi命令用来清除VSI的报文统计信息。

【命令】

reset l2vpn statistics vsi [ name vsi-name ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

name vsi-name：清除指定VSI的报文统计信息。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果不指定本参数，则清除所有VSI的信息。

【举例】

\# 清除本设备上所有VSI报文统计信息。

<Sysname> reset l2vpn statistics vsi

【相关命令】

· statistics enable (VSI view)


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1766628639.htm -->

hardware-resource vxlan命令用来配置VXLAN的硬件资源模式。

undo hardware-resource vxlan命令用来恢复缺省情况。

【命令】

hardware-resource vxlan { border8k | border16k | border24k | border32k | border40k | l2gw | l3gw8k | l3gw16k | l3gw24k | l3gw32k | l3gw40k }

undo hardware-resource vxlan

【缺省情况】

VXLAN的硬件资源模式为二层网关模式。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

border8k：Border模式，此模式下Overlay网络的邻接表占用8K资源。

border16k：Border模式，此模式下Overlay网络的邻接表占用16K资源。

border24k：Border模式，此模式下Overlay网络的邻接表占用24K资源。

border32k：Border模式，此模式下Overlay网络的邻接表占用32K资源。

border40k：Border模式，此模式下Overlay网络的邻接表占用40K资源。

l2gw：二层网关模式。

l3gw8k：三层网关模式，此模式下Overlay网络的邻接表占用8K资源。

l3gw16k：三层网关模式，此模式下Overlay网络的邻接表占用16K资源。

l3gw24k：三层网关模式，此模式下Overlay网络的邻接表占用24K资源。

l3gw32k：三层网关模式，此模式下Overlay网络的邻接表占用32K资源。

l3gw40k：三层网关模式，此模式下Overlay网络的邻接表占用40K资源。

【使用指导】

不同类型的设备上配置的硬件资源模式不同：

· 仅对报文进行二层转发的VTEP设备上，需要配置VXLAN的硬件资源模式为l2gw模式。

· 对报文进行三层转发的VXLAN IP网关设备上，需要配置VXLAN的硬件资源模式为l3gw8k、l3gw16k、l3gw24k、l3gw32k、l3gw40k模式。

· 对报文进行三层转发的Border设备上，需要配置VXLAN的硬件资源模式为border8k、border16k、border24k、border32k、border40k模式。

【举例】

\# 配置VXLAN的硬件资源模式为三层网关模式，且Overlay网络的邻接表占用8K资源。

<Sysname> system-view

[Sysname] hardware-resource vxlan l3gw8k

【相关命令】

· display hardware-resource vxlan


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1801149754.htm -->

service-instance命令用来创建以太网服务实例，并进入以太网服务实例视图。如果指定的以太网服务实例已经存在，则直接进入以太网服务实例视图。

undo service-instance命令用来删除指定的以太网服务实例。

【命令】

service-instance instance-id

undo service-instance instance-id

【缺省情况】

不存在以太网服务实例。

【视图】

二层以太网接口视图

二层聚合接口视图

【缺省用户角色】

network-admin

【参数】

instance-id：以太网服务实例的编号，取值范围为1～4096。

【举例】

\# 在二层以太网接口Ten-GigabitEthernet1/0/1上创建以太网服务实例1，并进入以太网服务实例1的视图。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] service-instance 1

[Sysname-Ten-GigabitEthernet1/0/1-srv1]

【相关命令】

· display l2vpn service-instance


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1803873614.htm -->

display l2vpn mac-address命令用来显示VSI的MAC地址表信息。

【命令】

display l2vpn mac-address [ vsi vsi-name ] [ dynamic ] [ count ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

vsi vsi-name：显示指定VSI的MAC地址表信息。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果不指定本参数，则显示所有VSI的MAC地址表信息。

dynamic：显示通过源MAC地址动态学习的MAC地址表项。如果不指定本参数，则显示所有类型的MAC地址表项，包括通过源MAC地址动态学习的本地和远端MAC地址表项、静态配置的远端MAC地址表项、通过OpenFlow下发的远端MAC地址表项和通过OVSDB生成的远端MAC地址表项。VXLAN不支持静态配置本地MAC地址表项。

count：显示MAC地址表项的数目。如果不指定本参数，则显示MAC地址表项的具体信息。

【举例】

\# 显示所有VSI的MAC地址表信息。

<Sysname> display l2vpn mac-address

MAC Address State VSI Name Link ID/Name Aging

0000-0000-000b Static vpn1 Tunnel10 NotAging

0000-0000-000c Dynamic vpn1 Tunnel60 Aging

0000-0000-000d Dynamic vpn1 Tunnel99 Aging

--- 3 mac address(es) found ---

\# 显示所有VSI的MAC地址表项总数。

<Sysname> display l2vpn mac-address count

3 mac address(es) found

表1-4 display l2vpn mac-address命令显示信息描述表

| XX mac address(es) found | VSI的MAC地址表项的总数 |
| --- | --- |

【相关命令】

· reset l2vpn mac-address


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1828563092.htm -->

reset l2vpn statistics ac命令用来清除AC的报文统计信息。

【命令】

reset l2vpn statistics ac [ interface interface-type interface-number service-instance instance-id ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

interface interface-type interface-number：清除指定二层接口上以太网服务实例的报文统计信息。interface-type interface-number表示接口类型和接口编号。

service-instance instance-id：清除指定以太网服务实例的报文统计信息。instance-id表示以太网服务实例的ID，取值范围为1～4096。

【使用指导】

执行本命令时，如果未指定任何参数，则清除所有AC的报文统计信息。

【举例】

\# 清除接口Ten-GigabitEthernet1/0/1上以太网服务实例1的报文统计信息。

<Sysname> reset l2vpn statistics ac interface ten-gigabitethernet 1/0/1 service-instance 1

【相关命令】

· display l2vpn service-instance verbose

· statistics enable (Ethernet service instance view)


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-1880502539.htm -->

display igmp host group命令用来显示IGMP执行主机行为的所有组播组信息。

【命令】

display igmp host group [ group-address | interface interface-type interface-number ] [ verbose ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

group-address：显示指定组播组的信息，取值范围为224.0.1.0～239.255.255.255。如果未指定本参数，则显示所有组播组的信息。

interface interface-type interface-number：显示指定接口上的信息。如果未指定本参数，则显示所有接口上的信息。

verbose：显示详细信息。如果未指定本参数，则显示简要信息。

【使用指导】

采用组播路由方式泛洪流量时，VXLAN组播报文源IP地址所在的接口需要作为IGMP主机加入VXLAN所在的组播组。通过本命令可以查看接口是否加入组播组，及该组播组的信息。

【举例】

\# 显示IGMP执行主机行为的所有组播组的简要信息。

<Sysname> display igmp host group

IGMP host groups in total: 2

 Vlan-interface10(1.1.1.20):

 IGMP host groups in total: 2

 Group address Member state Expires

 225.1.1.1 Idle Off

 225.1.1.2 Idle Off

\# 显示IGMP执行主机行为的所有组播组的详细信息。

<Sysname> display igmp host group verbose

 Vlan-interface10(1.1.1.20):

 IGMP host groups in total: 2

 Group: 225.1.1.1

 Group mode: Exclude

 Member state: Idle

 Expires: Off

 Source list (sources in total: 0):

 Group: 225.1.1.2

 Group mode: Exclude

 Member state: Idle

 Expires: Off

 Source list (sources in total: 0):

表1-3 display igmp host group命令显示信息描述表

| sources in total | 组播源的总数 |
| --- | --- |

对本命令的显示信息更加详细的介绍，请参见“IP组播配置指导”中的“IGMP”。

【相关命令】

· igmp host enable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-2010325582.htm -->

display vxlan tunnel命令用来显示与VXLAN关联的VXLAN隧道的信息。

【命令】

display vxlan tunnel [ vxlan-id vxlan-id ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

vxlan-id：显示与指定VXLAN关联的隧道的信息。vxlan-id为VXLAN的编号，取值范围为0～16777215。不指定此参数，则显示所有与VXLAN关联的隧道的信息。

【举例】

\# 显示所有与VXLAN关联的隧道的信息。

<Sysname> display vxlan tunnel

Total number of VXLANs: 1

VXLAN ID: 10, VSI name: vpna, Total tunnels: 3 (3 up, 0 down, 0 defect, 0 blocked)

Tunnel name Link ID State Type Flood proxy

Tunnel1 0x5000001 Up Manual Disabled

Tunnel2 0x5000002 Up Manual/Auto Disabled

MTunnel0 0x6002710 Up Auto Disabled

\# 显示与编号为10的VXLAN关联的隧道的信息。

<Sysname> display vxlan tunnel vxlan-id 10

VXLAN ID: 10, VSI name: vpna, Total tunnels: 3 (3 up, 0 down, 0 defect, 0 blocked)

Tunnel name Link ID State Type Flood proxy

Tunnel1 0x5000001 Up Manual Disabled

Tunnel2 0x5000002 Up Manual/Auto Disabled

MTunnel0 0x6002710 Up Auto Disabled

表1-9 display vxlan tunnel命令显示信息描述表

| Flood proxy | 隧道是否开启了泛洪代理功能，取值包括： · Enabled：开启隧道的泛洪代理功能。即该VXLAN内的广播、组播和未知单播流量将通过该Tunnel发送到代理服务器，由代理服务器进行复制并转发到其它远端VTEP · Disabled：关闭隧道的泛洪代理功能 |
| --- | --- |

【相关命令】

· tunnel

· vxlan


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-2125881637.htm -->

display hardware-resource vxlan命令用来显示VXLAN的硬件资源模式。

【命令】

display hardware-resource [ vxlan ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【使用指导】

执行本命令时，如果不指定vxlan参数，则显示所有类型的硬件资源模式。

【举例】

\# 显示VXLAN的硬件资源模式。

<Sysname> display hardware-resource vxlan

Vxlan resource(vxlan), all supported modes:

 l2gw L2 gateway--underlay/overlay 48K/0K

 l3gw8k L3 gateway--underlay/overlay 40K/8K

 l3gw16k L3 gateway--underlay/overlay 32K/16K

 l3gw24k L3 gateway--underlay/overlay 24K/24K

 l3gw32k L3 gateway--underlay/overlay 16K/32K

 l3gw40k L3 gateway--underlay/overlay 8K/40K

 border8k Border--underlay/overlay 40K/8K

 border16k Border--underlay/overlay 32K/16K

 border24k Border--underlay/overlay 24K/24K

 border32k Border--underlay/overlay 16K/32K

 border40k Border--underlay/overlay 8K/40K

 -----------------------------------------------

 Default Current Next

 l2gw border24k border24k

表1-2 display hardware-resource vxlan命令显示信息描述表

| Next | 最新配置的VXLAN硬件资源模式 |
| --- | --- |

【相关命令】

· hardware-resource vxlan


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-26756927.htm -->

reset l2vpn mac-address命令用来清除通过源MAC地址动态学习的MAC地址表项。

【命令】

reset l2vpn mac-address [ vsi vsi-name ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

vsi vsi-name：清除指定VSI动态学习的MAC地址表项。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果不指定本参数，则清除所有VSI动态学习的MAC地址表项。

【使用指导】

VSI通过源MAC地址学习到错误的MAC地址表项，或学习的MAC地址表项数目达到最大值时，可以执行本命令，以便重新学习MAC地址表项。

【举例】

\# 清除名为vpn1的VSI通过源MAC地址动态学习的MAC地址表项。

<Sysname> reset l2vpn mac-address vsi vpn1

【相关命令】

· display l2vpn mac-address vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-324158477.htm -->

description命令用来配置VSI的描述信息。

undo description命令用来恢复缺省情况。

【命令】

description text

undo description

【缺省情况】

未配置VSI的描述信息。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

text：VSI的描述信息，为1～80个字符的字符串，区分大小写。

【举例】

\# 配置名为vpn1的VSI的描述信息为“vsi for vpn1”。

<Sysname> system-view

[Sysname] vsi vpn1

[Sysname-vsi-vpn1] description vsi for vpn1

【相关命令】

· display l2vpn vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-367976968.htm -->

vxlan invalid-vlan-tag discard命令用来配置丢弃内层数据帧含有VLAN tag的VXLAN报文。

undo vxlan invalid-vlan-tag discard命令用来恢复缺省情况。

【命令】

vxlan invalid-vlan-tag discard

undo vxlan invalid-vlan-tag discard

【缺省情况】

不会检查VXLAN报文内层封装的以太网数据帧是否携带VLAN tag。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

远端VTEP上通过xconnect vsi命令的access-mode参数配置接入模式为ethernet时，VXLAN报文可能携带VLAN tag。这种情况下建议不要在本端VTEP上执行vxlan invalid-vlan-tag discard命令，以免错误地丢弃报文。

【举例】

\# 配置丢弃内层数据帧含有VLAN tag的VXLAN报文。

<Sysname> system-view

[Sysname] vxlan invalid-vlan-tag discard

【相关命令】

· vxlan invalid-udp-checksum discard

· xconnect vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-408578094.htm -->

vsi命令用来创建一个VSI，并进入VSI视图。如果指定的VSI已经存在，则直接进入VSI视图。

undo vsi命令用来删除指定的VSI。

【命令】

vsi vsi-name

undo vsi vsi-name

【缺省情况】

不存在VSI。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

vsi-name：VSI的名称，为1～31个字符的字符串，区分大小写。

【使用指导】

VSI是VTEP上为一个VXLAN提供二层交换服务的虚拟交换实例。VSI可以看做是VTEP上的一台基于VXLAN进行二层转发的虚拟交换机，它具有传统以太网交换机的所有功能，包括源MAC地址学习、MAC地址老化、泛洪等。VSI与VXLAN一一对应。

【举例】

\# 创建名为vxlan10的VSI，并进入VSI视图。

<Sysname> system-view

[Sysname] vsi vxlan10

[Sysname-vsi-vxlan10]

【相关命令】

· display l2vpn vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-619825245.htm -->

display arp suppression vsi命令用来显示VSI的ARP泛洪抑制表项信息。

【命令】

display arp suppression vsi [ name vsi-name ] [ slot slot-number ] [ count ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

name vsi-name：显示指定VSI的ARP泛洪抑制表项。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果不指定本参数，则显示所有VSI的ARP泛洪抑制表项。

slot slot-number：显示指定成员设备的ARP泛洪抑制表项。slot-number表示设备在IRF中的成员编号。如果不指定本参数，将显示主设备上的ARP泛洪抑制表项。

count：显示ARP泛洪抑制表项的个数。

【举例】

\# 显示VSI的ARP泛洪抑制表项信息。

<Sysname> display arp suppression vsi

IP address MAC address Vsi Name Link ID Aging

1.1.1.2 000f-e201-0101 vsi1 0x70000 14

1.1.1.3 000f-e201-0202 vsi1 0x80000 18

1.1.1.4 000f-e201-0203 vsi2 0x90000 10

\# 显示VSI的ARP泛洪抑制表项个数。

<Sysname> display arp suppression vsi count

Total entries: 3

表1-1 display arp suppression vsi命令显示信息描述表

| Total entries | ARP泛洪抑制表项的数目 |
| --- | --- |

【相关命令】

· arp suppression enable

· reset arp suppression vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-717866324.htm -->

reserved vxlan命令用来配置保留VXLAN。

undo reserved vxlan命令用来恢复缺省情况。

【命令】

reserved vxlan vxlan-id

undo reserved vxlan

【缺省情况】

未指定保留VXLAN。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

vxlan-id：保留VXLAN的ID，取值范围为0～16777215。

【使用指导】

只能在系统视图下配置一个全局保留VXLAN，该VXLAN不能与VSI下创建的VXLAN相同。

【举例】

\# 配置保留VXLAN为VXLAN 10000。

<Sysname> system-view

[Sysname] reserved vxlan 10000


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-761812436.htm -->

vxlan udp-port命令用来配置VXLAN报文的目的UDP端口号。

undo vxlan udp-port命令用来恢复缺省情况。

【命令】

vxlan udp-port port-number

undo vxlan udp-port

【缺省情况】

VXLAN报文的目的UDP端口号为4789。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

port-number：VXLAN报文的目的UDP端口号，取值范围为1～65535。建议不要将VXLAN报文的目的UDP端口号配置为知名端口，即1～1023之间的端口。

【使用指导】

属于同一个VXLAN的VTEP设备上需要配置相同的UDP端口号。

【举例】

\# 配置VXLAN报文的目的UDP端口号为6666。

<Sysname> system-view

[Sysname] vxlan udp-port 6666


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-783991409.htm -->

vxlan命令用来创建VXLAN，并进入VXLAN视图。如果指定的VXLAN已经存在，则直接进入VXLAN视图。

undo vxlan命令用来恢复缺省情况。

【命令】

vxlan vxlan-id

undo vxlan

【缺省情况】

不存在VXLAN。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

vxlan-id：VXLAN ID，取值范围为0～16777215。

【使用指导】

在一个VSI下只能创建一个VXLAN。不同VSI下创建的VXLAN，其VXLAN ID不能相同。

【举例】

\# 在名称为vpna的VSI下创建编号为10000的VXLAN，并进入VXLAN视图。

<Sysname> system-view

[Sysname] vsi vpna

[Sysname-vsi-vpna] vxlan 10000

[Sysname-vsi-vpna-vxlan-10000]

【相关命令】

· vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-839886575.htm -->

tunnel命令用来配置VXLAN与VXLAN隧道关联。

undo tunnel命令用来取消VXLAN与指定隧道的关联。

【命令】

tunnel { tunnel-number [ flooding-proxy ] | all }

undo tunnel { tunnel-number | all }

【缺省情况】

VXLAN未关联VXLAN隧道。

【视图】

VXLAN视图

【缺省用户角色】

network-admin

【参数】

tunnel-number：关联指定的VXLAN隧道。tunnel-number为隧道接口的编号，取值范围为0～8191。指定的隧道必须是VXLAN模式的隧道。

flooding-proxy：开启隧道的泛洪代理功能，即该VXLAN内的广播、组播和未知单播流量将通过该Tunnel发送到代理服务器，由代理服务器进行复制并转发到其它远端VTEP。如果未指定本参数，则表示关闭隧道的泛洪代理功能。

all：关联所有VXLAN隧道。

【使用指导】

在VXLAN组网中，用户可以手工将VXLAN与VXLAN隧道关联。VTEP接收到某个VXLAN的泛洪流量后，如果采用单播路由泛洪方式，则VTEP将在与该VXLAN关联的所有VXLAN隧道上发送该流量，以便将流量转发给所有的远端VTEP。

一个VXLAN可以关联多条VXLAN隧道；一条VXLAN隧道可以关联多个VXLAN。

配置泛洪代理功能时，需要注意：

· 不能通过重复执行本命令开启或关闭VXLAN隧道的泛洪代理功能。如需修改隧道的泛洪代理功能状态，请先通过undo tunnel命令取消VXLAN与指定隧道的关联，再执行tunnel命令。

· 一个VSI下可以配置多条开启泛洪代理功能的VXLAN隧道，第一个创建的VXLAN隧道作为主代理隧道，负责转发该VXLAN内的广播、组播和未知单播流量，其他隧道作为备用代理隧道，不转发流量。

执行tunnel all命令关联所有VXLAN隧道后，不能通过undo tunnel tunnel-number命令取消关联其中的一条VXLAN隧道，只能执行undo tunnel all命令同时取消关联所有的VXLAN隧道。

【举例】

\# 配置VXLAN隧道Tunnel1和Tunnel2与VXLAN 10000关联。

<Sysname> system-view

[Sysname] vsi vpna

[Sysname-vsi-vpna] vxlan 10000

[Sysname-vsi-vpna-vxlan-10000] tunnel 1

[Sysname-vsi-vpna-vxlan-10000] tunnel 2

【相关命令】

· display vxlan tunnel


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_-915231938.htm -->

reset arp suppression vsi命令用来清除VSI的ARP泛洪抑制表项。

【命令】

reset arp suppression vsi [ name vsi-name ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

name vsi-name：清除指定VSI的ARP泛洪抑制表项。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果不指定本参数，则清除所有VSI的ARP泛洪抑制表项。

【举例】

\# 清除所有VSI的ARP泛洪抑制表项。

<Sysname> reset arp suppression vsi

This command will delete all entries. Continue? [Y/N]:y

【相关命令】

· arp suppression enable

· display arp suppression vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1293405063.htm -->

mac-address static命令用来添加静态远端MAC地址表项。

undo mac-address static命令用来删除指定的静态远端MAC地址表项。

【命令】

mac-address static mac-address interface tunnel tunnel-number vsi vsi-name

undo mac-address static [ mac-address ] [ interface tunnel tunnel-number ] vsi vsi-name

【缺省情况】

不存在静态的远端MAC地址表项。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

mac-address：MAC地址，格式为H-H-H，不支持组播MAC地址和全0的MAC地址。在配置时，用户可以省去MAC地址中每段开头的“0”，例如输入“f-e2-1”即表示输入的MAC地址为“000f-00e2-0001”。

interface tunnel tunnel-number：指定远端MAC地址对应的VXLAN隧道接口。tunnel-number为VXLAN隧道接口的编号，只能指定设备上已创建的Tunnel接口的编号。

vsi vsi-name：指定远端MAC地址所属的VSI。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。

【使用指导】

远端MAC地址是指VTEP连接的远端站点内虚拟机的MAC地址。远端MAC地址既可以通过本命令静态配置，也可以通过报文中的源MAC地址动态学习。静态配置的远端MAC地址表项优先级高于源MAC地址动态学习的表项。

【举例】

\# 添加一条静态远端MAC地址表项：MAC地址为000f-e201-0101，VXLAN隧道接口为Tunnel1，MAC地址所属的VSI为vsi1。

<Sysname> system-view

[Sysname] mac-address static 000f-e201-0101 interface tunnel 1 vsi vsi1

【相关命令】

· vxlan tunnel mac-learning disable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1344362849.htm -->

vxlan local-mac report命令用来配置VXLAN增删本地MAC地址时记录日志。

undo vxlan local-mac report命令用来恢复缺省情况。

【命令】

vxlan local-mac report

undo vxlan local-mac report

【缺省情况】

VXLAN增删本地MAC地址时不会记录日志信息。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

执行vxlan local-mac report命令后，VXLAN增加或删除本地MAC地址时，将产生日志信息。生成的日志信息将被发送到设备的信息中心，通过设置信息中心的参数，决定日志信息的输出规则（即是否允许输出以及输出方向）。

【举例】

\# 配置VXLAN增删本地MAC地址时记录日志。

<Sysname> system-view

[Sysname] vxlan local-mac report


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1558979727.htm -->

shutdown命令用来关闭VSI。

undo shutdown命令用来开启VSI。

【命令】

shutdown

undo shutdown

【缺省情况】

VSI处于开启状态。

【视图】

VSI视图

【缺省用户角色】

network-admin

【使用指导】

关闭VSI后，该VSI将不能提供二层交换服务。

关闭VSI功能通常用于暂时禁用二层交换服务，但还需要再次启用该服务的场景。关闭VSI后，该VSI所有已存在的配置保持不变。在关闭状态下还可以对VSI进行配置。VSI再次被开启后，基于最新的配置提供二层交换服务。

【举例】

\# 关闭名为vpn1的VSI。

<Sysname> system-view

[Sysname] vsi vpn1

[Sysname-vsi-vpn1] shutdown

【相关命令】

· display l2vpn vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1645597014.htm -->

xconnect vsi命令用来将AC与VSI关联。

undo xconnect vsi命令用来恢复缺省情况。

【命令】

xconnect vsi vsi-name [ access-mode { ethernet | vlan } ] [ track track-entry-number&<1-3> ]

undo xconnect vsi

【缺省情况】

AC未关联VSI。

【视图】

以太网服务实例视图

【缺省用户角色】

network-admin

【参数】

vsi-name：VSI的名称，为1～31个字符的字符串，区分大小写。

access-mode：指定接入模式，缺省为VLAN接入模式。

ethernet：指定接入模式为Ethernet。

vlan：指定接入模式为VLAN。

track track-entry-number&<1-3>：配置AC与指定Track项联动。track-entry-number为Track项的序号，取值范围为1～1024；&<1-3>表示前面的参数最多可以输入3次。指定本参数后，仅当关联的Track项中至少有一个状态为positive时，AC的状态才会up；否则，AC的状态为down。

【使用指导】

某个接口的以太网服务实例视图下执行本命令后，从该接口接收到的、符合以太网服务实例报文匹配规则的报文，将通过查找关联VSI的MAC地址表进行转发。

在以太网服务实例下配置该命令前，必须先配置encapsulation命令。

接入模式分为以下两种：

· VLAN接入模式：从本地站点接收到的和发送给本地站点的以太网帧必须带有VLAN Tag。VTEP从本地站点接收到以太网帧后，删除该帧的所有VLAN Tag，再转发该数据帧；VTEP发送以太网帧到本地站点时，为其添加本地站点的VLAN Tag。采用该模式时，VTEP不会传递VLAN Tag信息，不同站点可以独立地规划自己的VLAN，不同站点的不同VLAN之间可以互通。

· Ethernet接入模式：从本地站点接收到的和发送给本地站点的以太网帧可以携带VLAN Tag，也可以不携带VLAN Tag。VTEP从本地站点接收到以太网帧后，保持该帧的VLAN Tag信息不变，转发该数据帧；VTEP发送以太网帧到本地站点时，不会为其添加VLAN Tag。采用该模式时，VTEP会在不同站点间传递VLAN Tag信息，不同站点的VLAN需要统一规划，否则无法互通。

执行本命令时需要注意，VLAN接入模式下，如果二层接口上只有一个匹配规则为default的以太网服务实例，则该接口接收到带有VLAN tag的数据帧后，设备会删除VLAN tag再转发该数据帧。如果该接口上还存在配置了其他匹配规则的以太网服务实例，则设备不会删除匹配encapsulation default规则的报文的VLAN tag。

【举例】

\# 接口Ten-GigabitEthernet1/0/1下采用以太网服务实例200来匹配外层VLAN为200的报文，将该以太网服务实例与名为vpn1的VSI关联。

<Sysname> system-view

[Sysname] vsi vpn1

[Sysname-vsi-vpn1] quit

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] service-instance 200

[Sysname-Ten-GigabitEthernet1/0/1-srv200] encapsulation s-vid 200

[Sysname-Ten-GigabitEthernet1/0/1-srv200] xconnect vsi vpn1

【相关命令】

· display l2vpn service-instance

· encapsulation

· vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1719919297.htm -->

display l2vpn vsi命令用来显示VSI的信息。

【命令】

display l2vpn vsi [ name vsi-name ] [ verbose ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

name vsi-name：显示指定VSI的信息。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果不指定本参数，则显示所有VSI的信息。

verbose：显示VSI的详细信息。如果不指定本参数，则显示VSI的简要信息。

【举例】

\# 显示所有VSI的简要信息。

<Sysname> display l2vpn vsi

Total number of VSIs: 1, 1 up, 0 down, 0 admin down

VSI Name VSI Index MTU State

vpna 0 1500 Up

表1-7 display l2vpn vsi命令显示信息描述表

| State | VSI的状态，取值包括： · Up：up状态。只有VXLAN关联了处于up状态的隧道和AC，VSI才会处于up状态 · Down：down状态 · Admin down：通过shutdown命令手工关闭VSI |
| --- | --- |

\# 显示所有VSI的详细信息。

<Sysname> display l2vpn vsi verbose

VSI Name: vpna

 VSI Index: 0

 VSI State: Up

 MTU: 1500

 Bandwidth: -

 Broadcast Restrain: 4294967295 kbps

 Multicast Restrain: 4294967295 kbps

 Unknown Unicast Restrain: 4294967295 kbps

 MAC Learning: Enabled

 MAC Table Limit: -

 MAC Learning rate: -

 Drop Unknown: -

 Flooding: Enabled

 Statistics: Enabled

 Input statistics:

 Octets: 0

 Packets: 0

 Errors: 0

 Discards: 0

 Output statistics:

 Octets: 0

 Packets: 0

 Errors: 0

 Discards: 0

 Gateway Interface: VSI-interface 100

 VXLAN ID: 10

 Tunnels:

 Tunnel Name Link ID State Type Flood proxy

 Tunnel1 0x5000001 Up Manual Disabled

 Tunnel2 0x5000002 Up Manual Disabled

 MTunnel0 0x6002710 Up Auto Disabled

 ACs:

 AC Link ID State

 XGE1/0/1 srv1000 0 Up

表1-8 display l2vpn vsi verbose命令显示信息描述表

| State | AC的状态，取值包括Up和Down |
| --- | --- |


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1804278458.htm -->

vxlan tunnel arp-learning disable命令用来关闭远端ARP自动学习功能。

undo vxlan tunnel arp-learning disable命令用来开启远端ARP自动学习功能。

【命令】

vxlan tunnel arp-learning disable

undo vxlan tunnel arp-learning disable

【缺省情况】

远端ARP自动学习功能处于开启状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

缺省情况下，设备从VXLAN隧道接收到报文后可以自动学习远端虚拟机的ARP信息，即远端ARP信息。在SDN控制器组网下，当控制器和设备间进行表项同步时，可以通过vxlan tunnel arp-learning disable命令暂时关闭远端ARP自动学习功能，以节省占用的设备资源。同步完成后，再执行undo vxlan tunnel arp-learning disable命令开启远端ARP自动学习功能。

建议用户只在控制器和设备间同步表项的情况下执行vxlan tunnel arp-learning disable命令。

【举例】

\# 关闭远端ARP自动学习功能。

<Sysname> system

[Sysname] vxlan tunnel arp-learning disable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1819286669.htm -->

tunnel bfd enable命令用来开启隧道的BFD检测功能。

undo tunnel bfd enable命令用来关闭隧道的BFD检测功能。

【命令】

tunnel bfd enable destination-mac mac-address

undo tunnel bfd enable

【缺省情况】

隧道的BFD检测功能处于关闭状态。

【视图】

VXLAN模式Tunnel接口视图

【缺省用户角色】

network-admin

【参数】

destination-mac mac-address：指定BFD报文的目的MAC地址为VXLAN隧道对端VTEP的桥MAC地址或组播MAC地址。mac-address为BFD报文的目的MAC地址，格式为H-H-H。在配置时，用户可以省去MAC地址中每段开头的“0”，例如输入“f-e2-1”即表示输入的MAC地址为“000f-00e2-0001”。

【使用指导】

隧道的BFD检测功能用来避免VTEP设备无法感知或无法及时感知隧道的故障，导致报文转发失败。隧道两端的VTEP设备上均需要开启该功能。VTEP设备周期性地通过VXLAN隧道向配置的目的MAC地址发送单跳BFD控制报文。如果在5秒内未接收到对端发送的BFD控制报文，则将隧道状态置为Defect，隧道接口状态仍为Up。VXLAN隧道故障排除后隧道状态将自动恢复为Up。

执行本命令的同时，还需要在系统视图下执行reserved vxlan命令配置保留VXLAN。否则，BFD会话无法up。

本命令不能与uRPF功能同时配置，否则，BFD会话无法up。关于uRPF功能的详细介绍请参见“安全配置指导”中的“uRPF”。

【举例】

\# 开启VXLAN隧道Tunnel9的BFD检测功能，并指定BFD报文的目的MAC地址为1-1-1。

<Sysname> system-view

[Sysname] interface tunnel 9 mode vxlan

[Sysname-Tunnel9] tunnel bfd enable destination-mac 1-1-1


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1900340857.htm -->

group命令用来配置VXLAN泛洪的组播地址和组播报文的源IP地址。

undo group命令用来恢复缺省情况。

【命令】

group group-address source source-address

undo group group-address source source-address

【缺省情况】

未指定VXLAN泛洪的组播地址和组播报文的源IP地址，VXLAN采用单播路由方式泛洪。

【视图】

VXLAN视图

【缺省用户角色】

network-admin

【参数】

group-address：VXLAN泛洪的组播地址，取值范围为224.0.1.0～239.255.255.255。

source source-address：指定VXLAN组播报文的源IP地址。

【使用指导】

数据中心网络中需要通过IP核心网络进行二层互联的站点较多时，采用组播路由方式可以节省泛洪流量对核心网络带宽资源的占用。

组播路由泛洪方式支持如下两种实现模式：

· PIM模式：在VTEP和核心设备上运行PIM协议，以建立组播转发表项。采用该模式时，可以使用Loopback接口地址作为组播报文的源IP地址。当VTEP存在多个网络侧接口时，PIM协议可以动态选择报文的出接口。

· IGMP主机模式：在VTEP上使能IGMP协议的主机功能、在连接VTEP的核心设备上配置IGMP、在所有核心设备上运行PIM协议，以建立组播转发表项。采用该模式时，必须使用VTEP上网络侧接口的IP地址作为组播报文的源IP地址，并在该接口上使能IGMP协议的主机功能。当VTEP存在多个网络侧接口时，IGMP主机模式只能采用组播报文的源IP地址所在的接口作为报文的出接口。

同一VXLAN网络中的不同VTEP可以采用不同的实现模式。

为确保组播报文转发正常，VXLAN组播报文的源IP地址（source-address）需要指定为一个已创建且处于up状态的VXLAN隧道的源端地址。

可以为不同的VXLAN指定相同的组播地址。例如，多个VXLAN共用相同的VTEP设备时，为这些VXLAN指定相同的组播地址，通过VXLAN ID来区分报文所属的VXLAN，可以减少IP核心网络中建立的组播转发表项数目。为不同VXLAN指定相同的组播地址时，要求为其指定的源IP地址也必须相同。

在同一个VXLAN视图下多次执行本命令，最后一次执行的命令生效。

【举例】

\# 为VXLAN 100配置VXLAN泛洪的组播地址为233.1.1.1、VXLAN组播报文的源IP地址为2.1.1.1。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] vxlan 100

[Sysname-vsi-aaa-vxlan-100] group 233.1.1.1 source 2.1.1.1

【相关命令】

· igmp host enable

· pim dm（IP组播命令参考/PIM）

· pim sm（IP组播命令参考/PIM）


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1901927086.htm -->

display l2vpn service-instance命令用来显示以太网服务实例的信息。

【命令】

display l2vpn service-instance [ interface interface-type interface-number [ service-instance instance-id ] ] [ verbose ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface interface-type interface-number：显示指定二层以太网接口或二层聚合接口上的以太网服务实例信息。interface-type interface-number为接口类型和接口编号。如果未指定本参数，则显示所有二层以太网接口和二层聚合接口上的以太网服务实例信息。

service-instance instance-id：显示指定以太网服务实例的信息。instance-id为以太网服务实例的ID，取值范围为1～4096。如果指定了interface interface-type interface-number参数，未指定本参数，则显示指定二层以太网接口或二层聚合接口上所有以太网服务实例的信息。

verbose：显示详细信息。如果未指定本参数，则显示简要信息。

【举例】

\# 显示所有以太网服务实例的简要信息。

<Sysname> display l2vpn service-instance

Total number of service-instances: 4, 4 up, 0 down

Total number of ACs: 2, 2 up, 0 down

Interface SrvID Owner LinkID State Type

XGE1/0/1 3 vsi12 1 Up VSI

XGE1/0/1 4 vsi13 1 Up VSI

表1-5 display l2vpn service-instance命令显示信息描述表

| Type | 以太网服务实例所属的L2VPN类型，取值为VSI |
| --- | --- |

\# 显示二层以太网接口Ten-GigabitEthernet1/0/1上所有以太网服务实例的详细信息。

<Sysname> display l2vpn service-instance interface ten-gigabitethernet 1/0/1 verbose

Interface: XGE1/0/1

 Service Instance: 1

 Encapsulation: s-vid 16

 VSI Name: vsi10

 Link ID: 1

 State: Up

 Statistics: Enabled

 Input Statistics:

 Octets:0

 Packets:0

 Output Statistics:

 Octets:0

 Packets:0

表1-6 display l2vpn service-instance verbose命令显示信息描述表

| Output Statistics | 出方向的以太网服务实例报文统计信息，包括出方向发送的字节数（Octets）、发送的报文数（Packets） |
| --- | --- |

【相关命令】

· service-instance


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1944169152.htm -->

statistics enable命令用来开启以太网服务实例的报文统计功能。

undo statistics enable命令用来关闭以太网服务实例的报文统计功能。

【命令】

statistics enable

undo statistics enable

【缺省情况】

以太网服务实例的报文统计功能处于关闭状态。

【视图】

以太网服务实例视图

【缺省用户角色】

network-admin

【使用指导】

只有为以太网服务实例配置了报文匹配方式并绑定了VSI实例，报文统计功能才会生效。如果在报文统计过程中修改报文匹配方式或绑定的VSI实例，则报文统计重新开始。

【举例】

\# 开启接口Ten-GigabitEthernet1/0/1上以太网服务实例200的报文统计功能。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] service-instance 200

[Sysname-Ten-GigabitEthernet1/0/1-srv200] statistics enable

【相关命令】

· display l2vpn service-instance verbose

· reset l2vpn statistics ac


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_1984545378.htm -->

vxlan tunnel mac-learning disable命令用来关闭远端MAC地址自动学习功能。

undo vxlan tunnel mac-learning disable命令用来开启远端MAC地址自动学习功能。

【命令】

vxlan tunnel mac-learning disable

undo vxlan tunnel mac-learning disable

【缺省情况】

远端MAC地址自动学习功能处于开启状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

如果网络中存在攻击，为了避免学习到错误的远端MAC地址，可以通过本命令手工关闭远端MAC地址自动学习功能。

【举例】

\# 关闭远端MAC地址自动学习功能。

<Sysname> system-view

[Sysname] vxlan tunnel mac-learning disable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_2131318877.htm -->

flooding disable命令用来关闭VSI的泛洪功能。

undo flooding disable命令用来开启VSI的泛洪功能。

【命令】

flooding disable { all | { broadcast | unknown-multicast | unknown-unicast } * }

undo flooding disable

【缺省情况】

VSI的泛洪功能处于开启状态。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

all：禁止广播、未知单播和未知组播数据帧向远端站点泛洪。

broadcast：禁止广播数据帧向远端站点泛洪。

unknown-multicast：禁止未知组播数据帧向远端站点泛洪。

unknown-unicast：禁止未知单播数据帧向远端站点泛洪。

【使用指导】

缺省情况下，VTEP从本地站点内接收到目的MAC地址为广播、未知单播和未知组播的数据帧后，会在该VXLAN内除接收接口外的所有本地接口和VXLAN隧道上泛洪该数据帧，将该数据帧发送给VXLAN内的所有站点。如果用户希望把某类数据帧限制在本地站点内，不通过VXLAN隧道将其转发到远端站点，则可以通过本命令手工禁止该类数据帧向远端站点泛洪。

【举例】

\# 关闭vsi1的广播数据帧泛洪功能。

<Sysname> system-view

[Sysname] vsi vsi1

[Sysname-vsi-vsi1] flooding disable broadcast


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_237131139.htm -->

statistics enable命令用来开启VSI的报文统计功能。

undo statistics enable命令用来关闭VSI的报文统计功能。

【命令】

statistics enable

undo statistics enable

【缺省情况】

VSI的报文统计功能处于关闭状态。

【视图】

VSI视图

【缺省用户角色】

network-admin

【举例】

\# 开启名为vsi1的VSI的报文统计功能。

<Sysname> system-view

[Sysname] vsi vsi1

[Sysname-vsi-vsi1] statistics enable

【相关命令】

· display l2vpn vsi verbose

· reset l2vpn statistics vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_366496077.htm -->

emulate-ping vxlan命令用来检测VXLAN内远端虚拟机的连通性。

【命令】

emulate-ping vxlan [ -c count | -m interval | -s packet-size | -t time-out ] * vxlan-id vxlan-id source-mac mac-address destination-mac mac-address

【视图】

任意视图

【缺省用户角色】

network-admin

【参数】

-c count：指定ICMP回显请求报文的发送次数，取值范围为1～4294967295，缺省值为5。

-m interval：指定发送ICMP回显请求报文的时间间隔，取值范围为1～65535，单位为毫秒，缺省值为200。

-s packet-size：指定发送的ICMP回显请求报文的长度（不包括IP和ICMP报文头），取值范围为20～8100，单位为字节，缺省值为56。

-t time-out：指定等待ICMP回显应答报文的超时时间，即设备发送ICMP回显请求报文time-out时长后，如果没有收到ICMP回显应答报文，则认为ICMP回显应答报文超时。time-out取值范围为0～65535，单位为毫秒，缺省值为2000。

vxlan-id vxlan-id：指定发送ICMP回显请求报文的VXLAN。vxlan-id表示VXLAN编号，取值范围为0～16777215。

source-mac mac-address：指定ICMP回显请求报文的源MAC地址。该地址必须是指定VXLAN的MAC地址表中已经存在的本端虚拟机MAC地址。

destination-mac mac-address：指定ICMP回显请求报文的目的MAC地址。该地址必须是指定VXLAN的MAC地址表中已经存在的远端虚拟机MAC地址。

【使用指导】

执行本命令后，设备将模拟本端虚拟机向远端虚拟机发送ICMP回显请求报文，该报文封装在二层数据帧中，并在指定的VXLAN内发送。本端设备根据是否收到ICMP回显应答报文、收到ICMP回显应答报文的时间，判断在该VXLAN内指定远端虚拟机是否可达，并输出相应的统计信息。

【举例】

\# 检测VXLAN 100内从MAC地址为1ea3-c0be-0206的本端虚拟机到MAC地址为1ea3-b77b-0106的远端虚拟机的连通性。

<Sysname> emulate-ping vxlan vxlan-id 100 source-mac 1ea3-c0be-0206 destination-mac 1ea3-b77b-0106

Emulate ping in VXLAN 100: source MAC 1ea3-c0be-0206, destination MAC 1ea3-b77b-0106, 56 data bytes.

Press CTRL_C to break.

56 bytes from 100.1.2.1: ICMP_seq=0 time=1.114 ms

56 bytes from 100.1.2.1: ICMP_seq=1 time=1.073 ms

56 bytes from 100.1.2.1: ICMP_seq=2 time=1.123 ms

56 bytes from 100.1.2.1: ICMP_seq=3 time=1.781 ms

56 bytes from 100.1.2.1: ICMP_seq=4 time=0.933 ms

--- Ping statistics for VXLAN 100 ---

5 packets transmitted, 5 packets received, 0.0% packet loss

Round-trip min/avg/max/std-dev=0.933/1.205/1.781/0.296 ms

表1-10 emulate-ping vxlan命令显示信息描述表

| Round-trip min/avg/max/std-dev=0.933/1.205/1.781/0.296 ms | 响应时间的最小值、平均值、最大值和标准方差，单位为毫秒 |
| --- | --- |


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_470693517.htm -->

igmp host enable命令用来在接口上开启IGMP协议的主机功能。

undo igmp host enable命令用来在接口上关闭IGMP协议的主机功能。

【命令】

igmp host enable

undo igmp host enable

【缺省情况】

接口上IGMP协议的主机功能处于关闭状态。

【视图】

接口视图

【缺省用户角色】

network-admin

【使用指导】

采用组播路由方式的IGMP主机模式泛洪流量时，必须在VXLAN组播报文源IP地址所在的接口上执行本命令，使得当前接口作为IGMP主机，即从该接口收到IGMP查询报文后，通过该接口发送组播组的报告报文，以便接收该组播组的报文。

只有通过multicast routing命令使能IP组播路由后，本命令才会生效。

【举例】

\# 使能公网实例中的IP组播路由，并在接口Vlan-interface10上开启IGMP协议的主机功能。

<Sysname> system-view

[Sysname] multicast routing

[Sysname-mrib] quit

[Sysname] interface vlan-interface 10

[Sysname-Vlan-interface10] igmp host enable

【相关命令】

· display igmp host group

· group

· multicast routing（IP组播命令参考/组播路由与转发）


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_502943338.htm -->

vxlan invalid-udp-checksum discard命令用来配置丢弃UDP校验和检查失败的VXLAN报文。

undo vxlan invalid-udp-checksum discard命令用来恢复缺省情况。

【命令】

vxlan invalid-udp-checksum discard

undo vxlan invalid-udp-checksum discard

【缺省情况】

不会检查VXLAN报文的UDP校验和。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

VTEP对二层数据帧进行封装时，将UDP校验和设置为0。缺省情况下，VTEP接收到VXLAN报文后，不会检查报文的UDP校验和。如果在VTEP上执行了本命令，则该VTEP会对接收的VXLAN报文的UDP校验和进行检查，校验和检查失败的报文将被丢弃。

为了兼容其他厂商的设备，UDP检验和为0和UDP检验和正确的报文均能通过VTEP的检查，被VTEP接收。

【举例】

\# 配置丢弃UDP校验和检查失败的VXLAN报文。

<Sysname> system-view

[Sysname] vxlan invalid-udp-checksum discard

【相关命令】

· vxlan invalid-vlan-tag discard


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_595735279.htm -->

l2vpn enable命令用来开启L2VPN功能。

undo l2vpn enable命令用来关闭L2VPN功能。

【命令】

l2vpn enable

undo l2vpn enable

【缺省情况】

L2VPN功能处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

只有开启L2VPN功能后，才能进行L2VPN的相关配置。

【举例】

\# 开启L2VPN功能。

<Sysname> system-view

[Sysname] l2vpn enable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_762789352.htm -->

encapsulation命令用来配置以太网服务实例的报文匹配规则。

undo encapsulation命令用来恢复缺省情况。

【命令】

encapsulation s-vid vlan-id [ c-vid { vlan-id-list | all } | only-tagged ]

encapsulation s-vid vlan-id-list [ c-vid vlan-id-list ]

encapsulation { default | tagged | untagged }

undo encapsulation

【缺省情况】

未配置报文匹配规则。

【视图】

以太网服务实例视图

【缺省用户角色】

network-admin

【参数】

s-vid：匹配外层VLAN标签（Service VLAN ID）为指定值的报文。

c-vid：匹配内层VLAN标签（Customer VLAN ID）为指定值的报文。

vlan-id：VLAN的编号，取值范围为1～4094。

vlan-id-list：VLAN列表，表示一个或多个VLAN的编号。表示方式为vlan-id-list = { vlan-id [ to vlan-id ] }&<1-8>。其中，vlan-id为指定VLAN的编号，取值范围为1～4094。&<1-8>表示前面的参数最多可以输入8次。

only-tagged：表示只匹配携带VLAN标签的报文。当匹配的VLAN为缺省VLAN时，如果未指定本关键字，则会同时匹配所携带VLAN标签为缺省VLAN的报文和未携带VLAN标签的报文；如果指定了本参数，则只匹配所携带VLAN标签为缺省VLAN的报文。

all：所有VLAN。

default：表示缺省的报文匹配规则。同一个以太网接口下最多只能有一个服务实例采用缺省的报文匹配规则。如果接口下同时存在一个采用缺省报文匹配规则的服务实例和多个采用其他报文匹配规则的服务实例，则未与任何其他报文匹配规则匹配的报文将匹配缺省报文匹配规则；如果接口下只存在一个采用缺省报文匹配规则的服务实例，则该接口上的所有报文都匹配缺省报文匹配规则。

tagged：表示匹配携带VLAN标签的报文。

untagged：表示匹配未携带VLAN标签的报文。

【使用指导】

二层以太网接口/二层聚合接口上某个以太网服务实例的匹配规则为encapsulation default时，如果该以太网服务实例的接入模式为VLAN模式，则该二层以太网接口/二层聚合接口上不能再创建其他的以太网服务实例；如果接入模式为Ethernet模式，则该二层以太网接口/二层聚合接口上可以创建其他的以太网服务实例，且接口上接收到的报文优先匹配其他的以太网服务实例，最后匹配encapsulation default所在的以太网服务实例。

如果同一接口的不同以太网服务实例上分别通过encapsulation s-vid vlan-id [ only-tagged ]命令和encapsulation s-vid vlan-id c-vid vlan-id命令配置匹配相同外层VLAN tag（s-vid）的报文匹配规则，则携带指定外层和内层VLAN tag的报文匹配encapsulation s-vid vlan-id c-vid vlan-id命令所属的以太网服务实例。

不能通过重复执行本命令修改报文匹配规则。如需修改报文匹配规则，请先通过undo encapsulation命令删除报文匹配规则，再执行encapsulation命令。

删除以太网服务实例下的报文匹配规则后，会自动取消以太网服务实例与VSI的关联。

在SDN组网中，如果执行本命令修改匹配的外层VLAN标签，则需要同时修改控制器通过Set-Field动作下发的VLAN ID，否则会导致命令行配置、发送到用户侧报文携带的VLAN标签与流表项不一致。

【举例】

\# 在二层以太网接口Ten-GigabitEthernet1/0/1的以太网服务实例1上配置如下报文匹配规则：匹配外层VLAN标签为111的报文。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] service-instance 1

[Sysname-Ten-GigabitEthernet1/0/1-srv1] encapsulation s-vid 111

【相关命令】

· display l2vpn service-instance


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1373885416_87075444.htm -->

restrain命令用来配置VSI的广播、组播或未知单播抑制带宽。

undo restrain命令用来恢复缺省情况。

【命令】

restrain { broadcast | multicast | unknown-unicast } bandwidth

undo restrain { broadcast | multicast | unknown-unicast }

【缺省情况】

VSI的广播、组播、未知单播抑制带宽均为4294967295kbps。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

broadcast：配置VSI的广播抑制带宽。

multicast：配置VSI的组播抑制带宽。

unknown-unicast：配置VSI的未知单播抑制带宽。未知单播报文是指在MAC地址表中不存在目的MAC地址对应表项的单播报文。

bandwidth：VSI的广播、组播或未知单播的抑制带宽值，取值范围为64～4194303，单位为kbps。

【使用指导】

当VSI内的广播、组播或未知单播流量超过配置的抑制带宽值时，将丢弃超过该值的广播、组播或未知单播流量。

【举例】

\# 配置名为vpn1的VSI的广播、组播、未知单播抑制带宽均为100kbps。

<Sysname> system-view

[Sysname] vsi vpn1

[Sysname-vsi-vpn1] restrain broadcast 100

[Sysname-vsi-vpn1] restrain multicast 100

[Sysname-vsi-vpn1] restrain unknown-unicast 100

【相关命令】

· display l2vpn vsi


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-1251739093.htm -->

arp distributed-gateway dynamic-entry synchronize命令用来开启分布式网关的动态ARP表项同步功能。

undo arp distributed-gateway dynamic-entry synchronize命令用来关闭分布式网关的动态ARP表项同步功能。

【命令】

arp distributed-gateway dynamic-entry synchronize

undo arp distributed-gateway dynamic-entry synchronize

【缺省情况】

分布式网关的动态ARP表项同步功能处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

mdc-admin

【使用指导】

分布式VXLAN IP网关上开启本地代理ARP功能时，本地网关不会将目标IP地址为分布式网关VSI虚接口的ARP报文转发给其他网关，只有本地网关能够学习到ARP报文发送者的ARP表项。如果希望所有网关都能学习到该ARP表项，需要开启分布式网关的动态ARP表项同步功能。

分布式VXLAN IP网关之间也可以通过控制器或EVPN等在彼此之间同步ARP表项，此时无需开启本功能。

【举例】

\# 开启分布式网关的动态ARP表项同步功能。

<Sysname> system-view

[Sysname] arp distributed-gateway dynamic-entry synchronize

【相关命令】

· distributed-gateway local

· local-proxy-arp enable（三层技术-IP业务命令参考/代理ARP）

· vxlan ip-forwarding


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-1666842994.htm -->

mtu命令用来配置接口的MTU值。

undo mtu命令用来恢复缺省情况。

【命令】

mtu size

undo mtu

【缺省情况】

接口的MTU为1500字节。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【参数】

size：接口的MTU值，取值范围为46～1500，单位为字节。

【举例】

\# 配置接口VSI-interface100的MTU值为1430字节。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] mtu 1430


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-1906697641.htm -->

shutdown命令用来关闭VSI虚接口。

undo shutdown命令用来开启VSI虚接口。

【命令】

shutdown

undo shutdown

【缺省情况】

VSI虚接口均处于开启状态。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【举例】

\# 关闭接口VSI-interface100。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] shutdown


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-511774785.htm -->

bandwidth命令用来配置接口的期望带宽。

undo bandwidth命令用来恢复缺省情况。

【命令】

bandwidth bandwidth-value

undo bandwidth

【缺省情况】

接口的期望带宽＝接口的波特率÷1000（kbps）。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【参数】

bandwidth-value：接口的期望带宽，取值范围为1～400000000，单位为kbps。

【使用指导】

期望带宽供业务模块使用，不会对接口实际带宽造成影响。

【举例】

\# 配置接口VSI-interface100的期望带宽为10000kbps。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] bandwidth 10000


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-635674563.htm -->

description命令用来配置接口的描述信息。

undo description命令用来恢复缺省情况。

【命令】

description text

undo description

【缺省情况】

接口的描述信息为“接口名 Interface”，例如：Vsi-interface100 Interface。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【参数】

text：接口的描述信息，为1～255个字符的字符串，区分大小写。

【举例】

\# 配置接口VSI-interface100的描述信息为“gateway for VXLAN 10”。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] description gateway for VXLAN 10


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-653593388.htm -->

display interface vsi-interface命令用来显示VSI虚接口的相关信息。

【命令】

display interface [ vsi-interface [ vsi-interface-id ] ] [ brief [ description | down ] ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

vsi-interface [ vsi-interface-id ]：指定VSI虚接口及其编号。vsi-interface-id为VSI虚接口的编号，只能指定设备上已创建的VSI虚接口的编号。如果不指定vsi-interface，则显示设备支持的所有接口的相关信息；如果指定vsi-interface，不指定vsi-interface-id，则显示所有VSI虚接口的信息。

brief：显示接口的概要信息。如果不指定该参数，则显示接口的详细信息。

description：用来显示用户配置的接口的全部描述信息。如果某接口的描述信息超过27个字符，不指定该参数时，只显示描述信息中的前27个字符，超出部分不显示；指定该参数时，可以显示全部描述信息。

down：显示当前物理状态为down的接口的信息以及down的原因。如果不指定该参数，则不会根据接口物理状态来过滤显示信息。

【举例】

\# 显示接口VSI-interface100的相关信息。

<Sysname> display interface vsi-interface 100

Vsi-interface100

Current state: UP

Line protocol state: UP

Description: Vsi-interface100 Interface

Bandwidth: 1000000kbps

Maximum transmission unit: 1500

Internet address: 10.1.1.1/24 (primary)

IP packet frame type: Ethernet II, hardware address: 0011-2200-0102

IPv6 packet frame type: Ethernet II, hardware address: 0011-2200-0102

Physical: Unknown, baudrate: 1000000 kbps

Last clearing of counters: Never

Last 300 seconds input rate: 0 bytes/sec, 0 bits/sec, 0 packets/sec

Last 300 seconds output rate: 0 bytes/sec, 0 bits/sec, 0 packets/sec

Input: 0 packets, 0 bytes, 0 drops

Output: 0 packets, 0 bytes, 0 drops

表1-11 display interface vsi-interface命令显示信息描述表

| Output: 0 packets, 0 bytes, 0 drops | 总计输出的报文数，总计输出的字节，总计丢弃的输出报文数 |
| --- | --- |

\# 显示所有VSI虚接口的概要信息。

<Sysname> display interface vsi-interface brief

Brief information on interfaces in route mode:

Link: ADM - administratively down; Stby - standby

Protocol: (s) - spoofing

Interface Link Protocol Primary IP Description

Vsi100 DOWN DOWN --

\# 显示接口VSI-interface100的概要信息，包括用户配置的全部描述信息。

<Sysname> display interface vsi-interface 100 brief description

Brief information on interfaces in route mode:Brief information of interface(s) under route mode:

Link: ADM - administratively down; Stby - standby

Protocol: (s) - spoofing

Interface Link Protocol Primary IP Description

Vsi100 UP UP 1.1.1.1 VSI-interface100

\# 显示当前状态为down的接口的信息以及DOWN的原因。

<Sysname> display interface brief down

Brief information on interfaces in route mode:

Link: ADM - administratively down; Stby - standby

Interface Link Cause

Vsi100 DOWN Administratively

Vsi200 DOWN Administratively

表1-12 display interface vsi-interface brief命令显示信息描述表

| Cause | 接口物理连接状态为down的原因，取值为： · Administratively：表示本链路被手工关闭了（配置了shutdown命令），需要执行undo shutdown命令才能恢复真实的物理状态 · Not connected：表示没有VSI关联该接口，或者关联该接口的VSI内没有AC或PW. |
| --- | --- |

【相关命令】

· reset counters interface vsi-interface


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-688525658.htm -->

mac-address命令用来配置VSI虚接口的MAC地址。

undo mac-address命令用来恢复缺省情况。

【命令】

mac-address mac-address

undo mac-address

【缺省情况】

VSI虚接口的MAC地址为设备上VLAN接口4094的MAC地址。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【参数】

mac-address：MAC地址，形式为H-H-H。

【举例】

\# 配置VSI虚接口100的MAC地址为0001-0001-0001。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] mac-address 1-1-1


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-719246472.htm -->

interface vsi-interface命令用来创建VSI虚接口，并进入VSI虚接口视图。如果指定的VSI虚接口已经存在，则直接进入VSI虚接口视图。

undo interface vsi-interface命令用来删除指定的VSI虚接口。

【命令】

interface vsi-interface vsi-interface-id

undo interface vsi-interface vsi-interface-id

【缺省情况】

不存在VSI虚接口。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

vsi-interface-id：VSI虚接口的编号，取值范围为1～99999。

【使用指导】

如果通过gateway vsi-interface命令将VSI虚接口指定为网关接口后，执行undo interface vsi-interface命令删除该VSI虚接口，则指定网关接口的配置也将删除。

【举例】

\# 创建VSI虚接口100，并进入VSI虚接口视图。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100]

【相关命令】

· gateway vsi-interface


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_-731443592.htm -->

reset counters interface vsi-interface命令用来清除VSI虚接口的统计信息。

【命令】

reset counters interface [ vsi-interface [ vsi-interface-id ] ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

vsi-interface [ vsi-interface-id ]：指定VSI虚接口及其编号。vsi-interface-id为VSI虚接口的编号，只能指定设备上已创建的VSI虚接口的编号。如果不指定vsi-interface，则清除设备支持的所有接口的统计信息；如果指定vsi-interface，不指定vsi-interface-id，则清除所有VSI虚接口的统计信息。

【使用指导】

在某些情况下，需要统计一定时间内某接口的流量，这就需要在统计开始前清除该接口原有的统计信息，重新进行统计。

【举例】

\# 清除接口VSI-interface100的统计信息。

<Sysname> reset counters interface vsi-interface 100

【相关命令】

· display interface vsi-interface


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_1401427343.htm -->

vtep group member local命令用来将本设备加入VXLAN IP网关保护组，并配置本设备的成员地址。

undo vtep group member local命令用来取消本设备加入指定的VXLAN IP网关保护组。

【命令】

vtep group group-ip member local member-ip

undo vtep group group-ip member local

【缺省情况】

设备未加入VXLAN IP网关保护组。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

group-ip：VXLAN IP网关保护组的VTEP IP地址，该地址必须是本设备上已经存在的地址。

member-ip：本设备在VXLAN IP网关保护组内的成员地址，该地址必须是设备上已经配置的地址。

【使用指导】

成员地址不能和保护组的VTEP IP相同；同一个保护组中不同成员的成员地址也不能相同。

【举例】

\# 配置本设备加入VXLAN IP保护组，保护组的VTEP IP地址是1.1.1.1，本设备的成员地址为2.2.2.2。

<Sysname> system-view

[Sysname] vtep group 1.1.1.1 member local 2.2.2.2

【相关命令】

· vtep group member remote


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_1786221006.htm -->

vtep group member remote命令用来配置VXLAN IP网关保护组的成员地址列表。

undo vtep group member remote命令用来删除指定VXLAN IP网关保护组的成员地址列表。

【命令】

vtep group group-ip member remote member-ip&<1-8>

undo vtep group group-ip member remote

【缺省情况】

未配置VXLAN IP网关保护组的成员地址列表。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

group-ip：VXLAN IP网关保护组的VTEP IP地址。

member-ip&<1-8>：VXLAN IP网关保护组成员IP地址列表。&<1-8>表示最多可以输入8个IP地址，每个IP地址之间用空格分隔。

【举例】

\# 配置VXLAN IP网关保护组1.1.1.1包含的成员设备为2.2.2.2、3.3.3.3和4.4.4.4。

<Sysname> system-view

[Sysname] vtep group 1.1.1.1 member remote 2.2.2.2 3.3.3.3 4.4.4.4

【相关命令】

· vtep group member local


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_1907797907.htm -->

arp send-rate命令用来开启VSI虚接口的ARP报文发送限速功能。

undo arp send-rate命令用来关闭VSI虚接口的ARP报文发送限速功能。

【命令】

arp send-rate pps

undo arp send-rate

【缺省情况】

VSI虚接口的ARP报文发送限速功能处于关闭状态。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【参数】

pps：ARP报文发送限速速率，取值范围为1～500，单位为包每秒（pps）。

【使用指导】

开启VSI虚接口的ARP报文发送限速功能后，如果VSI虚接口的ARP报文发送速率超过限制的值，则后续待发送的ARP报文将被丢弃，直到接口的APP发送速率低于限速速率。

虚拟机的报文处理能力较弱，通过本配置可以控制VTEP发往虚拟机的ARP报文速率，以免影响虚拟机工作。

【举例】

\# 配置VSI虚接口1的ARP报文发送限速为50pps。

<Sysname> system

[Sysname] interface vsi-interface 1

[Sysname-Vsi-interface1] arp send-rate 50


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_281389180.htm -->

gateway subnet命令用来配置VSI所属的子网网段。

undo gateway subnet命令用来删除VSI所属的子网网段。

【命令】

gateway subnet { ipv4-address wildcard-mask | ipv6-address prefix-length }

undo gateway subnet { ipv4-address wildcard-mask | ipv6-address prefix-length }

【缺省情况】

未指定VSI所属的子网网段。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

ipv4-address：IPv4子网网段地址，为点分十进制格式。

wildcard-mask：IPv4地址掩码的反码，即将IPv4地址的掩码取反（0变1，1变0）。例如：子网掩码255.0.0.0的反码为0.255.255.255。其中，反码中的“1”表示忽略IPv4地址中对应的位，“0”表示必须保留此位。

ipv6-address prefix-length：IPv6地址及前缀长度。prefix-length为IPv6前缀长度，取值范围为1～128。

【使用指导】

在VSI视图下配置子网网段前，必须先为该VSI指定网关接口。取消为VSI指定网关接口时，会自动删除为该VSI指定的子网网段。

一个VSI视图下最多可以配置8个子网网段，包括IPv4子网和IPv6子网。

【举例】

\# 配置名称为vxlan的VSI所属的子网网段为100.0.10.0/24。

<Sysname> system-view

[Sysname] vsi vxlan

[Sysname-vsi-vxlan] gateway subnet 100.0.10.0 0.0.0.255


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_397073433.htm -->

default命令用来恢复接口的缺省配置。

【命令】

default

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【使用指导】

接口下的某些配置恢复到缺省情况后，会对设备上当前运行的业务产生影响。建议您在执行该命令前，完全了解其对网络产生的影响。

您可以在执行default命令后通过display this命令确认执行效果。对于未能成功恢复缺省的配置，建议您查阅相关功能的命令手册，手工执行恢复该配置缺省情况的命令。如果操作仍然不能成功，您可以通过设备的提示信息定位原因。

【举例】

\# 将接口VSI-interface100恢复为缺省配置。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] default

This command will restore the default settings. Continue? [Y/N]:y


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_481301059.htm -->

gateway vsi-interface命令用来为VSI指定网关接口。

undo gateway vsi-interface命令用来恢复缺省情况。

【命令】

gateway vsi-interface vsi-interface-id

undo gateway vsi-interface

【缺省情况】

未指定VSI的网关接口。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

vsi-interface-id：VSI网关虚接口的编号，取值范围为1～99999。

【使用指导】

本命令中指定的VSI网关虚接口必须已经通过interface vsi-interface命令创建。如果将VSI虚接口指定为网关接口后，执行undo interface vsi-interface命令删除该VSI虚接口，则指定网关接口的配置也将删除。

一个VSI只能指定一个网关接口。

不同的VSI不能指定相同的网关接口。

【举例】

\# 为VSI指定网关接口为Vsi-interface100。

<Sysname> system-view

[Sysname] vsi vpna

[Sysname-vsi-vpna] gateway vsi-interface 100

【相关命令】

· interface vsi-interface


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1435133935_709885613.htm -->

distributed-gateway local命令用来配置VSI虚接口为分布式网关接口。

undo distributed-gateway local命令用来恢复缺省情况。

【命令】

distributed-gateway local

undo distributed-gateway local

【缺省情况】

VSI虚接口不是分布式网关接口。

【视图】

VSI虚接口视图

【缺省用户角色】

network-admin

【使用指导】

在分布式VXLAN IP网关组网中，多个网关上同一VXLAN的VSI虚接口需要配置相同的IP地址。为了避免IP地址冲突，需要在VSI虚接口上执行本命令，以防止VSI虚接口上报地址冲突，导致VSI虚接口不可用。

【举例】

\# 配置接口Vsi-interface100为分布式网关接口。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] distributed-gateway local


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_-1118816267.htm -->

ovsdb server bootstrap ca-certificate命令用来指定与控制器进行SSL通信时使用的CA证书文件。

undo ovsdb server bootstrap ca-certificate命令用来恢复缺省情况。

【命令】

ovsdb server bootstrap ca-certificate ca-filename

undo ovsdb server bootstrap ca-certificate

【缺省情况】

与控制器进行SSL通信时使用PKI域中的CA证书文件。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

ca-filename：表示与控制器进行SSL通信时使用的CA证书文件名称，不区分大小写，文件名称中不允许出现slot字样。只允许使用主用主控板的CA证书文件。

【使用指导】

通过本命令指定与控制器进行SSL通信使用的CA证书文件时，如果已经开启了OVSDB服务器，则该配置不会生效。只有关闭并重新开启OVSDB服务器后，该配置才会生效。

本命令指定的只能是主用主控板中的CA证书文件。如果指定的文件存在，直接使用。否则，使用开启OVSDB服务器时通过SSL连接获取的自签名证书，并通过本命令指定证书文件名。

执行本命令后，优先使用本命令指定的CA证书文件，不使用PKI域中的CA证书。

【举例】

\# 指定与控制器进行SSL通信时使用的CA证书文件为ca-new。

<Sysname> system-view

[Sysname] ovsdb server bootstrap ca-certificate ca-new

【相关命令】

· ovsdb server enable

· ovsdb server pki domain

· ovsdb server pssl

· ovsdb server ssl


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_-48450165.htm -->

vxlan tunnel flooding-proxy命令用来开启组播隧道泛洪代理功能。

undo vxlan tunnel flooding-proxy命令用来关闭组播隧道泛洪代理功能。

【命令】

vxlan tunnel flooding-proxy

undo vxlan tunnel flooding-proxy

【缺省情况】

组播隧道泛洪代理功能处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

开启组播隧道泛洪代理功能后，系统会将控制器下发的组播隧道转换为具有泛洪代理功能的隧道。VXLAN内的广播、组播和未知单播流量将通过具有泛洪代理功能的隧道发送到泛洪代理服务器，由代理服务器进行复制并转发到其他远端VTEP。

采用泛洪代理（服务器复制）方式转发站点间的泛洪流量时，必须开启该功能。

执行undo vxlan tunnel flooding-proxy命令，不会改变已有隧道的泛洪代理模式。

【举例】

\# 开启组播隧道泛洪代理功能。

<Sysname> system

[Sysname] vxlan tunnel flooding-proxy


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_-66681395.htm -->

ovsdb server pki domain命令用来指定与控制器进行SSL通信时使用的PKI域。

undo ovsdb bootstrap server pki domain命令用来恢复缺省情况。

【命令】

ovsdb server pki domain domain-name

undo ovsdb server pki domain

【缺省情况】

未指定与控制器进行SSL通信时使用的PKI域。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

domain-name：表示与控制器进行SSL通信时使用的PKI域名称，为1～31个字符的字符串，区分大小写。指定的PKI域必须存在，并且PKI域中包含完整的证书和密钥。PKI域的详细介绍，请参见“安全配置指导”中的“PKI”。

【使用指导】

与控制器进行SSL通信时需通过本命令指定PKI域。

通过本命令指定与控制器进行SSL通信时使用的PKI域时，如果已经开启了OVSDB服务器，则该配置不会生效。只有关闭并重新开启OVSDB服务器后，该配置才会生效。

【举例】

\# 指定与控制器进行SSL通信时使用的PKI域为ovsdb_test。

<Sysname> system-view

[Sysname] ovsdb server pki domain ovsdb_test

【相关命令】

· ovsdb server bootstrap ca-certificate

· ovsdb server enable

· ovsdb server pssl

· ovsdb server ssl


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_-996557706.htm -->

ovsdb server ptcp命令用来配置与控制器建立被动TCP连接。

undo ovsdb server ptcp命令用来恢复缺省情况。

【命令】

ovsdb server ptcp [ port port-number ]

undo ovsdb server ptcp

【缺省情况】

不会与控制器建立被动TCP连接。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

port port-number：指定与控制器建立TCP连接的监听端口号，取值范围为1～65535，如果不指定本参数，则监听6640端口。

【使用指导】

通过本命令配置与控制器建立被动TCP连接时，如果已经开启了OVSDB服务器，则该配置不会生效。只有关闭并重新开启OVSDB服务器后，该配置才会生效。

只能配置一个OVSDB服务器监听的TCP连接端口号。多次执行本命令，最后一次执行的命令生效。

【举例】

\# 配置与控制器建立被动TCP连接，监听端口号采用默认端口号。

<Sysname> system-view

[Sysname] ovsdb server ptcp

【相关命令】

· ovsdb server enable

· ovsdb server tcp


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_1608756831.htm -->

ovsdb server ssl命令用来配置与控制器建立主动SSL连接。

undo ovsdb server ssl命令用来删除指定的主动SSL连接。

【命令】

ovsdb server ssl ip ip-address port port-number

undo ovsdb server ssl ip ip-address port port-number

【缺省情况】

不会与控制器建立主动SSL连接。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

ssl ip-address：指定SSL连接的目的IP地址。

port port-number：指定SSL连接的目的端口号，取值范围为1～65535。

【使用指导】

配置与控制器建立主动SSL连接前，需先指定SSL通信中使用的PKI域。

通过本命令配置与控制器建立主动SSL连接时，如果已经开启了OVSDB服务器，则该配置不会生效。只有关闭并重新开启OVSDB服务器后，该配置才会生效。

OVSDB服务器最多只能配置8个与控制器的SSL主动连接。

【举例】

\# 配置与控制器建立主动SSL连接，指定目的IP地址为192.168.12.2、目的端口号为6632。

<Sysname> system-view

[Sysname] ovsdb server ssl ip 192.168.12.2 port 6632

【相关命令】

· ovsdb server bootstrap ca-certificate

· ovsdb server enable

· ovsdb server pki domain

· ovsdb server pssl


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_1634544501.htm -->

ovsdb server enable命令用来开启OVSDB服务器。

undo ovsdb server enable命令用来关闭OVSDB服务器。

【命令】

ovsdb server enable

undo ovsdb server enable

【缺省情况】

OVSDB服务器处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

开启OVSDB服务器后，OVSDB服务器可以与控制器建立连接，接收控制器通过OVSDB控制协议发送的数据，并保存到本地OVSDB数据库中，从而实现控制器对VTEP设备进行VXLAN相关配置。

为了保证OVSDB服务器能够与控制器建立连接，在开启OVSDB服务器前，必须先配置至少一条与控制器的连接。

【举例】

\# 开启OVSDB服务器。

<Sysname> system-view

[Sysname] ovsdb server enable


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_2005517305.htm -->

vtep access port命令用来指定当前接口为用户侧的接入端口。

undo vtep access port命令用来恢复缺省情况。

【命令】

vtep access port

undo vtep access port

【缺省情况】

当前接口不是用户侧的接入端口。

【视图】

二层以太网接口视图

二层聚合接口视图

【缺省用户角色】

network-admin

【使用指导】

只有将接口配置为用户侧的接入端口后，控制器上才能够显示该端口并对其进行控制。

【举例】

\# 指定二层以太网接口Ten-GigabitEthernet1/0/1为用户侧的接入端口。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] vtep access port


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_485297701.htm -->

ovsdb server pssl命令用来配置与控制器建立被动SSL连接。

undo ovsdb server pssl命令用来恢复缺省情况。

【命令】

ovsdb server pssl [ port port-number ]

undo ovsdb server pssl

【缺省情况】

不会与控制器建立被动SSL连接。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

port port-number：指定与控制器建立SSL连接的端口号，OVSDB服务器监听该端口上的SSL连接请求。port-number取值范围为1～65535。如果不指定本参数，则监听6640端口。

【使用指导】

配置与控制器建立被动SSL连接前，需先指定SSL通信中使用的PKI域。

通过本命令配置与控制器建立被动SSL连接时，如果已经开启了OVSDB服务器，则该配置不会生效。只有关闭并重新开启OVSDB服务器后，该配置才会生效。

只能配置一个OVSDB服务器监听的SSL连接端口号。多次执行本命令，最后一次执行的命令生效。

【举例】

\# 配置与控制器建立被动SSL连接，监听端口号采用默认端口号。

<Sysname> system-view

[Sysname] ovsdb server pssl

【相关命令】

· ovsdb server bootstrap ca-certificate

· ovsdb server enable

· ovsdb server pki domain

· ovsdb server ssl


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_710379611.htm -->

ovsdb server tcp命令用来配置与控制器建立主动TCP连接。

undo ovsdb server tcp命令用来删除指定的主动TCP连接。

【命令】

ovsdb server tcp ip ip-address port port-number

undo ovsdb server tcp ip ip-address port port-number

【缺省情况】

不会与控制器建立主动TCP连接。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

ip ip-address：指定TCP连接的目的IP地址。

port port-number：指定TCP连接的目的端口号。

【使用指导】

通过本命令配置与控制器建立主动TCP连接时，如果已经开启了OVSDB服务器，则该配置不会生效。只有关闭并重新开启OVSDB服务器后，该配置才会生效。

OVSDB服务器最多只能配置8个与控制器的TCP主动连接。

【举例】

\# 配置与控制器建立主动TCP连接，指定目的IP地址为192.168.12.2、目的端口号为6632。

<Sysname> system-view

[Sysname] ovsdb server tcp ip 192.168.12.2 port 6632

【相关命令】

· ovsdb server enable

· ovsdb server ptcp


---

<!-- 13-VXLAN命令参考/html/-1039092092_1068952525_-1605669940_833707484.htm -->

vtep enable命令用来开启OVSDB VTEP服务。

undo vtep enabl命令用来关闭OVSDB VTEP服务。

【命令】

vtep enable

undo vtep enable

【缺省情况】

OVSDB VTEP服务处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【举例】

\# 开启设备的OVSDB VTEP服务。

<Sysname> system-view

[Sysname] vtep enable


---

<!-- 13-VXLAN命令参考/html/00-前言.htm -->

前 言

本命令参考主要介绍S6800系列以太网交换机的VXLAN配置命令。

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
