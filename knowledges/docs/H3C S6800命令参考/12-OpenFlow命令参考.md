# 12-OpenFlow命令参考

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1334094552.htm -->

mac-ip dynamic-mac aware命令用来配置支持动态MAC地址。

undo mac-ip dynamic-mac aware命令用来恢复缺省情况。

【命令】

mac-ip dynamic-mac aware

undo mac-ip dynamic-mac aware

【缺省情况】

不支持动态MAC地址，即忽略控制器下发的此类消息。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

此功能仅在支持MAC-IP流表情况下，决定是否支持控制器在查询或者删除流表项时包含动态MAC地址（动态MAC表项变化不需要上报控制器）。

【举例】

\# 配置实例1支持动态MAC地址。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] mac-ip dynamic-mac aware


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1401480557.htm -->

controller auxiliary命令用来配置辅助连接。

undo controller auxiliary命令用来删除指定的辅助连接。

【命令】

controller controller-id auxiliary auxiliary-id transport { tcp | udp | ssl ssl-policy-name } [ address { ip ipv4-address | ipv6 ipv6-address } ] [ port port-number ]

undo controller id auxiliary auxiliary-id

【缺省情况】

不存在辅助连接。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

controller-id：控制器的ID号，取值范围为0～63。

auxiliary auxiliary-id：辅助连接编号，取值范围为1～255。

transport：传输类型。

tcp：TCP连接。

udp：UDP连接。

ssl ssl-policy-name：SSL策略的名称，为1～31字符的字符串，不区分大小写。

ip ipv4-address：控制器的IPv4地址。

ipv6 ipv6-address：控制器的IPv6地址。

port port-number：控制器的端口号，取值范围为1～65535，缺省值为6633。

【使用指导】

OpenFlow通道可以由一个主连接和多个辅助连接组成。辅助连接用于提高控制器和OpenFlow交换机的通信能力。

辅助连接命令行和主连接命令行不做额外的检查处理。如果配置冲突，辅助连接将无法建立。

辅助连接的目的地址和端口号可以和主连接不一致。目的地址和端口号未配置时，和主连接一致。

【举例】

\# 为实例1下编号为10控制器配置编号为1的辅助连接。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] controller 10 auxiliary 1 transport tcp


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1483487384.htm -->

fail-open mode命令用来配置交换机与控制器连接中断时的运行模式。

undo fail-open mode命令用来恢复缺省情况。

【命令】

fail-open mode { secure | smart | standalone }

undo fail-open mode

【缺省情况】

OpenFlow实例建立时，缺省为Secure模式，且为该实例下发Table Miss表项（动作为drop）。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

secure：Secure模式，连接断开后，交换机根据流表项转发。匹配的流表项中执行output controller动作转发的流量，会被丢弃。

smart：Smart模式，连接断开后，交换机根据流表项转发。匹配的流表项中执行output controller动作转发的流量，会进行正常转发。

standalone：Standalone模式，连接断开后，交换机正常转发。

【举例】

\# 配置交换机与控制器连接中断时的运行模式为Standalone模式。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] fail-open mode standalone


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1555371044.htm -->

classification命令用来配置OpenFlow实例的类型。

undo classification命令用来恢复缺省情况。

【命令】

classification { global | vlan vlan-id [ mask vlan-mask ] [ loosen ] }

undo classification

【缺省情况】

未配置OpenFlow实例的类型。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

global：全局实例。

vlan：VLAN实例，实例按VLAN划分。

vlan-id：VLAN ID，取值范围为1～4094。

vlan-mask：VLAN掩码，取值范围为0～4095，缺省值为4095。

loosen：loosen模式。配置loosen模式后，如果接口所在VLAN与实例配置VLAN存在交集，则接口就属于OpenFlow实例。未配置loosen模式时，只有当实例配置的VLAN是接口所在VLAN的子集，该接口才属于OpenFlow实例。

【使用指导】

多次执行本命令，最后一次执行的命令生效。

VLAN & mask为实际生效VLAN区间。mask比特位为1表示符合，可以不连续；比特位为0表示忽略。生效VLAN区间，可通过display openflow instance查看。

【举例】

\# 配置OpenFlow VLAN实例1对应的VLAN为255，掩码为7。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] classification vlan 255 mask 7

【相关命令】

· display openflow instance


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1627710014.htm -->

tcp dscp命令用来配置OpenFlow报文的DSCP值。

undo tcp dscp命令用来恢复缺省情况。

【命令】

tcp dscp dscp-value

undo tcp dscp

【缺省情况】

未配置OpenFlow报文的DSCP值。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

dscp-value：OpenFlow报文的DSCP值，取值范围为0～63。

【举例】

\# 配置OpenFlow报文的DSCP值为63。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] tcp dscp 63


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1658323696.htm -->

listening port命令用来为OpenFlow实例启动SSL服务器。

undo listening port命令用来恢复缺省情况。

【命令】

listening port port-number ssl ssl-policy-name

undo listening port

【缺省情况】

OpenFlow实例下没有启动SSL服务器。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

port-number：服务器的端口号，取值范围为1～65535。

ssl ssl-policy-name：SSL服务器端策略的名称，为1～31字符的字符串，不区分大小写。

【使用指导】

没有启动SSL服务器时，设备作为TCP/SSL客户端主动连接控制器（SSL服务器，需要相应配置）；启动SSL服务器之后，设备作为SSL服务器端被动等待控制器（SSL客户端）连接。

不能通过重复执行本命令修改OpenFlow实例启动的SSL服务器。如需修改，请先通过undo listening port命令删除OpenFlow实例启动的SSL服务器， 再执行listening port命令重新启动SSL服务器。

【举例】

\# 为OpenFlow实例1启动端口号为20000的SSL服务器。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] listening port 20000 ssl ssl_name


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1662715998.htm -->

controller address命令用来配置主连接。

undo controller address命令用来删除指定的主连接。

【命令】

controller controller-id address { ip ipv4-address | ipv6 ipv6-address } [ port port-number ] [ local address { ip local-ipv4-address | ipv6 local-ipv6-address } [ port local-port-number ] ] [ ssl ssl-policy-name ] [ vrf vrf-name ]

undo controller controller-id address

【缺省情况】

不存在主连接。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

controller-id：控制器的ID号，取值范围为0～63。

ip ipv4-address：控制器的IPv4地址。

ipv6 ipv6-address：控制器的IPv6地址。

port port-number：控制器建立连接使用的端口号，取值范围为1～65535，缺省值为6633。

local address：交换机与控制器连接的源IP地址。如果交换机与控制器之间存在多条路由可达，当交换机进行主备倒换时或者重启后，希望通过原来的路由重新建立连接，而不是新选择的路由，此时可以通过本参数进行配置。

ip local-ipv4-address：源IPv4地址。

ipv6 local-ipv6-address：源IPv6地址。

port local-port-number：源端口号，取值范围为1～65535，缺省值为随机分配的值。

ssl ssl-policy-name：安全连接的客户端安全策略，用于控制器认证交换机，每个控制器连接配置独立的安全策略。ssl-policy-name为1～31个字符的字符串，不区分大小写。

vrf vrf-name：指定控制器所在的VRF，vrf-name表示MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则表示控制器位于公网中。

【使用指导】

多次执行该命令可以添加多个控制器，与每个控制器仅允许建立一个主连接。

主连接一般用于控制消息的处理（下发流表项、获取数据、信息上报等）。

建议控制器的IP地址使用单播地址，否则交换机和控制器之间可能无法建立连接。

建议源IP地址使用单播地址，且该IP地址是OpenFlow实例下一个端口的IP地址，否则交换机和控制器之间可能无法建立连接。

【举例】

\# 配置实例1的控制器1的IP地址为1.1.1.1，端口号为6666。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] controller 1 address ip 1.1.1.1 port 6666


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1724270988.htm -->

display openflow summary命令用来显示OpenFlow实例的概要信息。

【命令】

display openflow summary

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【举例】

\# 显示OpenFlow概要信息。

<Sysname> display openflow summary

Fail-open mode: Se - Secure mode, Sa - Standalone mode

ID Status Datapath-ID Channel Table-num Port-num Reactivate

1 Active 0x0000000100001221 Connected 2 8 N

10 Inactive - - - - -

4094 Active 0x00000ffe00001221 Failed(Sa) 2 0 N

表1-10 display openflow summary命令显示信息描述表

| Reactivate | 是否需要重新激活该OpenFlow实例： · N：配置未改变，不需要重新激活 · 未激活该OpenFlow实例时，显示为“-” |
| --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1763325043.htm -->

display openflow instance命令用来显示OpenFlow实例的详细信息。

【命令】

display openflow instance [ instance-id ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。如果未指定本参数，将显示所有实例的详细信息。

【举例】

\# 显示OpenFlow实例100的详细信息。

<Sysname> display openflow instance

Instance 100 information:

Configuration information:

 Description: test-desc

 Active status: Active

 Inactive configuration:

 None

 Active configuration:

 Classification: VLAN, loosen mode, total VLANs(1)

 2

 In-band management VLAN, total VLANs(0)

 Empty VLAN

 Connect mode: Multiple

 MAC address learning: Disabled

 TCP DSCP value: 10

 Flow table:

 Table ID(type): 0(MAC-IP), count: 0

 Flow-entry max-limit: 65535

 Datapath ID: 0x0000001234567891

 Default table-miss: Drop

 Forbidden port: None

 Qinq Network: Disabled

 TCP connection backup: Enabled

Port information:

 Ten-GigabitEthernet1/0/3

Active channel information:

 Controller 1 IP address: 192.168.49.49 port: 6633

 Controller 2 IP address: 192.168.43.49 port: 6633

表1-8 display openflow instance命令显示信息描述表

| Failopen mode | 连接中断时的运行模式： · Standalone：Standalone模式 · Smart：Smart模式 · Secure：Secure模式 |
| --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-1818483643.htm -->

openflow instance命令用来创建OpenFlow实例，并进入OpenFlow实例视图。如果指定的OpenFlow实例已经存在，则直接进入OpenFlow实例视图。

undo openflow instance命令用来删除OpenFlow实例。

【命令】

openflow instance instance-id

undo openflow instance instance-id

【缺省情况】

不存在OpenFlow实例。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。

【举例】

\# 创建OpenFlow实例1，并进入OpenFlow实例视图。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1]


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-2053662283.htm -->

in-band management vlan命令用来配置带内管理VLAN。

undo in-band management vlan命令用来恢复缺省情况。

【命令】

in-band management vlan { vlan-id [ to vlan-id ] } &<1-10>

undo in-band management vlan

【缺省情况】

未配置带内管理VLAN。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

vlan-id：VLAN ID，取值范围为1～4094。

【使用指导】

缺省情况下，OpenFlow实例内的VLAN都是进行OpenFlow转发的，实例无法通过这些VLAN与控制器建立连接。配置带内管理VLAN后，这些VLAN内流量是正常转发的，可以用于实例与控制器建立连接。

【举例】

\# 在实例1中配置VLAN 10为带内管理VLAN。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] in-band management vlan 10


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-243819836.htm -->

display openflow flow-table命令用来显示OpenFlow实例的流表信息。

【命令】

display openflow instance instance-id flow-table [ table-id ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。

table-id：流表ID，取值范围为0～254。如果未指定本参数，将显示所有流表的信息。

【举例】

\# 显示OpenFlow实例100的所有流表信息。

<Sysname> display openflow instance 100 flow-table

Instance 100 flow table information:

Table 0 information:

 Table type: MAC-IP, flow entry count: 1, total flow entry count: 2

MissRule (default) flow entry information:

 cookie: 0x0, priority: 0, hard time: 0, idle time: 0, flags: reset_counts

 |no_pkt_counts|no_byte_counts, byte count: --, packet count: --

Match information: any

Instruction information:

 Write actions:

 Drop

Flow entry rule 1 information:

 cookie: 0x0, priority: 1, hard time: 0, idle time: 0, flags: none,

 byte count: --, packet count: --

Match information:

 Ethernet destination MAC address: 0000-0000-0001

 Ethernet destination MAC address mask: ffff-ffff-ffff

 VLAN ID: 100, mask: 0xfff

Instruction information:

 Write actions:

 Output interface: XGE1/0/4

 Write metadata/mask: 0x0000000000000001/0xffffffffffffffff

 Goto table: 1

Table 1 information:

 Table type: Extensibility, flow entry count: 2, total flow entry count: 2

MissRule (default) flow entry information:

 cookie: 0x0, priority: 0, hard time: 0, idle time: 0, flags: none,

 byte count: --, packet count: 60

Match information: any

Instruction information:

 Write actions:

 Drop

Flow entry rule 1 information: (Not effective)

 cookie: 0x0, priority: 0, hard time: 0, idle time: 0, flags: flow_send_rem

 |check_overlap, byte count: --, packet count: 1

Match information:

 Input interface: XGE1/0/3

 Ethernet source MAC address: 0000-0000-0001

 Ethernet source MAC address mask: ffff-ffff-ffff

Instruction information:

 Set meter: 100

 Apply actions:

 Output interface: XGE1/0/4

 Write actions:

 Output interface: Controller, send length: 128 bytes

表1-3 display openflow flow-table命令显示信息描述表

| Instruction information | 动作指令集信息： · Set meter：应用指定的Meter表 · Goto table：进入下一级流表 · Clear actions：清除动作集中的所有动作 · Apply actions：立即执行动作序列中的动作 · Write actions：更改动作集中的所有动作 更多信息，请参见[表1-5](#_Ref349812331) |
| --- | --- |

表1-4 流表项匹配规则信息

| Experiment | 无 | 扩展匹配项： · Address ID：地址区分ID |
| --- | --- | --- |

表1-5 流表项动作类型

| Set field | 修改报文指定的域 |
| --- | --- |

表1-6 流表项端口类型

| （端口名称） | 支持 | 支持 | 实例有效端口，包含物理接口和逻辑接口 |
| --- | --- | --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-529750882.htm -->

display openflow auxiliary命令用来显示OpenFlow实例的辅助连接信息和收发的报文统计信息等。

【命令】

display openflow instance instance-id auxiliary [ controller-id [ auxiliary auxiliary-id ] ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance instance-id：OpenFlow实例号，取值范围为1～4094。

controller-id：控制器编号，取值范围为0～63。

auxiliary auxiliary-id：辅助连接编号，取值范围为1～255。

【举例】

\# 显示OpenFlow实例100的控制器辅助连接信息。

<Sysname> display openflow instance 100 auxiliary

Controller ID: 1 Auxiliary connection number: 2

 Auxiliary connection ID: 1

 Controller IP address: 192.168.49.48

 Controller port: 6633

 Connect type: TCP

 Connect state: Established

 Packets sent: 9

 Packets received: 9

 SSL policy: --

 Auxiliary connection ID: 2

 Controller IP address: 192.168.49.49

 Controller port: 6633

 Connect type: TCP

 Connect state: Established

 Packets sent: 9

 Packets received: 9

 SSL policy: --

表1-2 display openflow auxiliary命令显示信息描述表

| SSL policy | 用于SSL连接的SSL客户端策略的名称，--表示未配置 |
| --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-623650641.htm -->

default table-miss permit命令用来配置OpenFlow实例缺省的table miss动作为进行正常二三层转发。

undo default table-miss permit命令用来恢复缺省情况。

【命令】

default table-miss permit

undo default table-miss permit

【缺省情况】

缺省table miss动作为丢弃。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【举例】

\# 配置OpenFlow实例1的缺省table miss动作。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] default table-miss permit


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-864262542.htm -->

qinq-network enable命令用来配置QINQ模式。

undo qinq-network enable命令用来恢复缺省情况。

【命令】

qinq-network enable

undo qinq-network enable

【缺省情况】

未配置QINQ模式，带有双层VLAN Tag的报文通过Extensibility表之后，只带一个内层的VLAN Tag。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

配置本功能后，带有双层VLAN Tag的报文通过Extensibility表之后，还是会带双层VLAN Tag。

【举例】

\# 配置QINQ模式。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] qinq-network enable

【相关命令】

· flow-table


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-916432023.htm -->

openflow shutdown命令用来开启OpenFlow的关闭接口功能。

undo openflow shutdown命令用来恢复缺省情况。

【命令】

openflow shutdown

undo openflow shutdown

【缺省情况】

OpenFlow的关闭接口功能处于关闭状态。

【视图】

二层以太网接口视图

【缺省用户角色】

network-admin

【使用指导】

开启本功能后，可以通过display interface命令查看到接口显示信息中Current state为OFP DOWN。

开启本功能后，除了通过undo openflow shutdown命令打开接口，还可以通过收到控制器下发的PORT_MOD消息来打开接口。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上配置OpenFlow的关闭接口功能。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] openflow shutdown


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_-957123623.htm -->

permit-port-type member-port命令用来允许流表中添加聚合成员端口。

undo permit-port-type命令用来恢复缺省情况。

【命令】

permit-port-type member-port

undo permit-port-type

【缺省情况】

不允许流表中添加聚合成员端口。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【举例】

\# 允许流表中添加聚合成员端口。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] permit-port-type member-port


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1082185858.htm -->

loop-protection enable命令用来使能环路保护功能。

undo loop-protection enable命令用来恢复缺省情况。

【命令】

loop-protection enable

undo loop-protection enable

【缺省情况】

环路保护功能处于关闭状态。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

用户将OpenFlow实例去激活之后，OpenFlow下发一条流表项，用于丢弃实例所属VLAN范围内的所有流量，从而避免环路。

【举例】

\# 配置实例1使能环路保护功能。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] loop-protection enable


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1137555395.htm -->

precedence dynamic arp命令用来配置允许ARP报文修改OpenFlow ARP表项。

undo precedence dynamic命令用来恢复缺省情况。

【命令】

precedence dynamic arp

undo precedence dynamic arp

【缺省情况】

不允许ARP报文修改OpenFlow ARP表项。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

本功能仅支持MAC-IP流表。

配置本功能后，动态ARP表项的优先级高于OpenFlow ARP表项，即OpenFlow ARP表项可以被动态ARP表项覆盖。

【举例】

\# 配置OpenFlow实例1允许ARP报文修改OpenFlow ARP表项。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] precedence dynamic arp


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1174025551.htm -->

description命令用来配置OpenFlow实例的描述信息。

undo description命令用来恢复缺省情况。

【命令】

description text

undo description

【缺省情况】

未配置OpenFlow实例的描述信息。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

text：OpenFlow实例的描述信息，为1～255个字符的字符串，区分大小写。

【举例】

\# 配置实例1的描述信息为test-desc。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] description test-desc


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1340580145.htm -->

flow-table命令用来配置OpenFlow实例下的流表。

undo flow-table命令用来恢复缺省情况。

【命令】

flow-table { [ ingress-vlan ingress-table-id ] [ extensibility extensibility-table-id | mac-ip mac-ip-table-id ] * [ egress-vlan egress-table-id ] }

undo flow-table

【缺省情况】

OpenFlow实例包含一个Extensibility流表，流表ID为0。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

ingress-vlan ingress-table-id：表示入方向添加VLAN Tag流表。ingress-table-id为Ingress-vlan流表ID，取值范围为0～254。

extensibility extensibility-table-id：Extensibility流表ID，取值范围为0～254。

mac-ip mac-ip-table-id：MAC-IP流表ID，取值范围为0～254。

egress-vlan egress-table-id：表示出方向剥离VLANTag流表。egress-table-id为Egress-vlan流表ID，取值范围为0～254。

【使用指导】

用户激活实例之前配置当前实例将要使用的流表类型以及与之对应的流表ID。

多次执行本命令，最后一次执行的命令生效。

输入的Extensibility流表ID要大于MAC-IP流表ID。

ingress-vlan和egress-vlan可以单独配置，也可以和mac-ip、extensibility一起配置，一起配置的时候，ingress-vlan和egress-vlan必须是首尾两表。另外，只有在配置了QINQ模式，并且设备处于Standalone模式时，ingress-vlan和egress-vlan这两个流表才生效。

【举例】

\# 配置实例1流表类型为MAC-IP表ID为0，Extensibility表ID为1。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] flow-table mac-ip 0 extensibility 1

【相关命令】

· qinq-network enable


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1352600301.htm -->

controller mode命令用来配置实例内的多个控制器的连接模式。

undo controller mode命令用来恢复缺省情况。

【命令】

controller mode { multiple | single }

undo controller mode

【缺省情况】

连接模式为Multiple。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

multiple：多连接模式。

single：单连接模式。

【使用指导】

当连接模式是Single时，一次仅连接一个控制器，其它作为备份，仅当连接断开才根据ID顺序连接备份控制器。

当连接模式为Multiple时，同时连接所有控制器，当一个或者多个控制器失效或者连接断开时，仍然能保证OpenFlow交换机正常工作。

【举例】

\# 配置实例1的控制器连接模式为Single。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] controller mode single


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1408034386.htm -->

controller connect interval命令用来配置OpenFlow实例与控制器重连尝试的时间间隔。

undo controller connect interval命令用来恢复缺省情况。

【命令】

controller connect interval interval

undo controller connect interval

【缺省情况】

OpenFlow实例与控制器重连尝试的时间间隔为60秒。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

interval：重连尝试的时间间隔，取值范围为10～120，单位为秒。

【举例】

\# 配置实例1与控制器重连尝试的时间间隔为10秒。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] controller connect interval 10


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1482690.htm -->

mac-learning forbidden命令用来在实例配置的VLAN上禁止MAC地址学习。

undo mac-learning forbidden命令用来恢复缺省情况。

【命令】

mac-learning forbidden

undo mac-learning forbidden

【缺省情况】

实例配置的VLAN上允许MAC地址学习。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【举例】

\# 配置实例1禁止MAC地址学习。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] mac-learning forbidden


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1621631081.htm -->

refresh ip-flow命令用来刷新OpenFlow实例下MAC-IP流表的三层表项。

【命令】

refresh ip-flow

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

某些情况下，MAC-IP流表的三层表项会被覆盖，此时需要手工执行本命令刷新MAC-IP流表，重新从控制器获取新的三层表项。

【举例】

\# 刷新OpenFlow实例1下MAC-IP流表的三层表项。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] refresh ip-flow


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1909500161.htm -->

active instance命令用来激活OpenFlow实例。

undo active instance命令用来取消激活OpenFlow实例。

【命令】

active instance

undo active instance

【缺省情况】

未激活OpenFlow实例。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

新配置的实例信息（如VLAN配置、Table配置）必须通过重新激活实例来生效。若当前实例已经与控制器建立连接，激活新配置后会重新建立连接。

【举例】

\# 激活OpenFlow实例1。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] active instance


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_1941934673.htm -->

reset openflow instance statistics命令用来清除控制器发送和接收报文的统计计数。

【命令】

reset openflow instance instance-id { controller [ controller-id ] | listened } statistics

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。

controller-id：控制器的ID号，取值范围为0～63。如果未指定本参数，则清除实例下所有控制器发送和接收报文的统计计数。

listened：实例启动的服务端连接的客户端。

【举例】

\# 清除OpenFlow实例1对应的所有控制器发送和接收报文的统计计数。

<Sysname> reset openflow instance 1 controller statistics


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_19692254.htm -->

display openflow group命令用来显示OpenFlow实例的Group表项信息。

【命令】

display openflow instance instance-id group [ group-id ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。

group-id：Group ID，取值范围为0～4294967040。如果未指定本参数，将显示实例所有Group表项的信息。

【举例】

\# 显示OpenFlow实例100的Group表项信息。

<Sysname> display openflow instance 100 group

Instance 100 group table information:

 Group count: 2

Group entry 103:

 Type: All, byte count: 55116, packet count: 401

 Bucket 1 information:

Action count 1, watch port: any, watch group: any

Byte count 55116, packet count 401

 Output interface: BAGG100

 Bucket 2 information:

 Action count 1, watch port: any, watch group: any

 Byte count --, packet count --

 Output interface: Controller, send length: 128 bytes

 Referenced information:

 Count: 3

 Flow table 0

 Flow entry: 1, 2, 3

Group entry 104:

 Type: All, byte count: 0, packet count: 0

 Bucket 1 information:

 Action count 1, watch port: any, watch group: any

 Byte count --, packet count --

 Output interface: Controller, send length: 128 bytes

 Referenced information:

 Count: 0

表1-7 display openflow group命令显示信息描述表

| Flow entry | 引用Group表项的流表项ID列表 |
| --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_2061144415.htm -->

tcp-connection backup命令用来开启OpenFlow连接备份功能。

undo tcp-connection backup命令用来关闭OpenFlow连接备份功能。

【命令】

tcp-connection backup

undo tcp-connection backup

【缺省情况】

OpenFlow连接备份功能处于开启状态。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

本功能通过备份OpenFlow连接信息，使设备在发生主备倒换时保持OpenFlow连接。

本功能只在基于TCP的OpenFlow连接上有效。

【举例】

\# 关闭OpenFlow实例1的OpenFlow连接备份功能。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] undo tcp-connection backup


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_2103369972.htm -->

forbidden port命令用来配置禁止上送Controller的端口类型。

undo forbidden port命令用来恢复缺省情况。

【命令】

forbidden port { l3-physical-interface | vlan-interface | vsi-interface } *

undo forbidden port

【缺省情况】

所有接口都上送Controller。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

l3-physical-interface：三层以太网接口。

vlan-interface：VLAN接口。

vsi-interface：VXLAN中的VSI虚接口。

【举例】

\# 配置OpenFlow实例1禁止上送VLAN接口。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] forbidden port vlan-interface


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_253137497.htm -->

display openflow meter命令用来显示OpenFlow实例的Meter表项信息。

【命令】

display openflow instance instance-id meter [ meter-id ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。

meter-id：Meter ID，取值范围为1～4294901760。如果未指定本参数，将显示实例所有Meter表项的信息。

【举例】

\# 显示OpenFlow实例100的Meter表项信息。

<Sysname> display openflow instance 100 meter

Meter flags: KBPS -- Rate value in kb/s, PKTPS -- Rate value in packet/sec

 BURST -- Do burst size, STATS -- Collect statistics

Instance 100 meter table information:

 meter entry count: 2

Meter entry 100 information:

 Meter flags: KBPS

 Band 1 information

 Type: drop, rate: 1024, burst size: 65536

 Byte count: --, packet count: --

 Referenced information:

 Count: 3

 Flow table: 0

 Flow entry: 1, 2, 3

Meter entry 200 information:

 Meter flags: KBPS

 Band 1 information

 Type: drop, rate: 10240, burst size: 655360

 Byte count: --, packet count: --

 Referenced information:

 Count: 0

表1-9 display openflow meter命令显示信息描述表

| Flow entry | 引用Meter表项的流表项ID列表 |
| --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_292787754.htm -->

controller echo-request interval命令用来配置发送Echo request报文的时间间隔。

undo controller echo-request interval命令用来恢复缺省情况。

【命令】

controller echo-request interval interval

undo controller echo-request interval

【缺省情况】

发送Echo request报文的时间间隔为5秒。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

interval：发送Echo request报文的时间间隔，取值范围为1～10，单位为秒。

【举例】

\# 配置实例1发送Echo request报文的时间间隔为10秒。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] controller echo-request interval 10


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_358295652.htm -->

flow-log disable命令用来关闭流表项变化成功后打印日志的开关。

undo flow-log disable命令用来恢复缺省情况。

【命令】

flow-log disable

undo flow-log disable

【缺省情况】

流表项变化成功后打印日志的开关处于开启状态。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【举例】

\# 关闭OpenFlow实例1流表项变化成功后打印日志的开关。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] flow-log disable


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_479435900.htm -->

protocol-packet filter slow命令用来配置匹配慢速协议报文的高优先级流表项，动作为丢弃。

undo protocol-packet filter命令用来恢复缺省情况。

【命令】

protocol-packet filter slow

undo protocol-packet filter

【缺省情况】

未配置匹配慢速协议报文的高优先级流表项。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【使用指导】

匹配慢速协议报文的高优先级流表项优先级高于控制器下发的流表项。

慢速协议目前支持LACP、LAMP和OAM协议。

【举例】

\# 配置匹配慢速协议报文的高优先级流表项，动作为drop。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] protocol-packet filter slow


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_658580261.htm -->

datapath-id命令用来配置OpenFlow实例的Datapath ID。

undo datapath-id命令用来恢复缺省情况。

【命令】

datapath-id id

undo datapath-id

【缺省情况】

OpenFlow实例的Datapath ID是由实例ID和设备桥MAC组成，前16个比特是实例ID，后48个比特是设备桥MAC。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

id：OpenFlow实例的Datapath ID，取值范围为十六进制数1～ffffffffffffffff。

【举例】

\# 配置实例1的Datapath ID为123456。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] datapath-id 123456


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_759671421.htm -->

flow-entry max-limit命令用来配置Extensibility表的流表项的最大个数。

undo flow-entry max-limit命令用来恢复缺省情况。

【命令】

flow-entry max-limit limit-value

undo flow-entry max-limit

【缺省情况】

Extensibility表的流表项的最大个数为65535。

【视图】

OpenFlow实例视图

【缺省用户角色】

network-admin

【参数】

limit-value：流表项的最大个数。取值范围为1～65535。

【举例】

\# 配置Extensibility表的流表项的最大个数为256。

<Sysname> system-view

[Sysname] openflow instance 1

[Sysname-of-inst-1] flow-entry max-limit 256


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_760469714.htm -->

display openflow命令用来显示OpenFlow实例对应的控制器信息。

【命令】

display openflow instance instance-id { controller [ controller-id ] | listened }

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance-id：OpenFlow实例号，取值范围为1～4094。

controller-id：控制器的ID号，取值范围为0～63。如果未指定本参数，将显示实例下所有控制器的信息。

listened：实例启动的服务端连接的客户端。

【举例】

\# 显示OpenFlow实例100对应的控制器信息。

<Sysname> display openflow instance 100 controller

OpenFlow instance ID: 100

 Reconnect interval: 60 (s)

 Echo interval: 5 (s)

 Controller ID: 1

 Controller IP address: 192.168.49.49

 Controller port: 6633

 Local IP address: 192.0.0.1

 Local port: 5566

 Controller role: Equal

 Connect type: TCP

 Connect state: Established

 Packets sent: 9

 Packets received: 9

 SSL policy: --

 VRF name: --

表1-1 display openflow controller命令显示信息描述表

| VRF name | 控制器所在的VRF名称，--表示未配置 |
| --- | --- |


---

<!-- 12-OpenFlow命令参考/html/-1285007378_1761225522_-825919948_988040848.htm -->

openflow lossless enable命令用来开启OpenFlow的无丢包模式。

undo openflow lossless enable命令用来关闭OpenFlow的无丢包模式。

【命令】

openflow lossless enable

undo openflow lossless enable

【缺省情况】

OpenFlow的无丢包模式处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

在OpenFlow场景中，OpenFlow的流表下发过程中设备可能会出现丢包，从而引发很多问题，比如流量误上送Controller，导致误下发OpenFlow表项等，此时需要开启OpenFlow的无丢包模式。在无丢包模式下，设备不会丢包，OpenFlow在实际网络中可以正常使用，但是匹配能力会受限制，比如不能匹配IPv6地址。

在非OpenFlow场景中，请不要开启OpenFlow的无丢包模式，否则会影响转发效率和能力级匹配。

要使配置生效，必须在配置后重启设备。在重启设备前，请保存当前配置。

【举例】

\# 开启OpenFlow的无丢包模式。

<Sysname> system-view

[Sysname] openflow lossless enable

 Enable lossless traffic function? [Y/N]:y

 For the setting to take effect, save the configuration, and then reboot the device.


---

<!-- 12-OpenFlow命令参考/html/00-前言.htm -->

前 言

本命令参考主要介绍了S6800系列交换机OpenFlow相关的配置命令。

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
