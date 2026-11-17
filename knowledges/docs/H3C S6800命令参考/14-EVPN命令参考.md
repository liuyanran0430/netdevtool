# 14-EVPN命令参考

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-13639716.htm -->

arp mac-learning disable命令用来配置禁止EVPN从ARP信息中学习MAC地址表项。

undo arp mac-learning disable命令用来恢复缺省情况。

【命令】

arp mac-learning disable

undo arp mac-learning disable

【缺省情况】

EVPN可以从ARP信息中学习MAC地址表项。

【视图】

EVPN实例视图

【缺省用户角色】

network-admin

【使用指导】

VTEP可能会同时接收到远端VTEP通告的MAC地址信息和ARP信息。其中，ARP信息中包含MAC地址信息。为了避免重复，可以在VTEP上执行本命令禁止EVPN从ARP信息中学习MAC地址表项，EVPN仅通过MAC地址信息学习远端MAC地址表项。

【举例】

\# 配置禁止EVPN从ARP信息中学习MAC地址表项。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] evpn encapsulation vxlan

[Sysname-vsi-aaa-evpn-vxlan] arp mac-learning disable


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-1591857670.htm -->

policy vpn-target命令用来开启BGP EVPN路由的VPN-Target过滤功能。

undo policy vpn-target命令用来关闭BGP EVPN路由的VPN-Target过滤功能。

【命令】

policy vpn-target

undo policy vpn-target

【缺省情况】

BGP EVPN路由的VPN-Target过滤功能处于开启状态。

【视图】

BGP EVPN地址族视图

【缺省用户角色】

network-admin

【使用指导】

开启BGP EVPN路由的VPN-Target过滤功能后，设备只将Export Route Target属性与本地Import Route Target属性匹配的EVPN路由加入到BGP EVPN路由表。设备上如需保存所有BGP EVPN路由，则需执行undo policy vpn-target命令，不对BGP EVPN路由进行VPN-Target过滤。

【举例】

\# 关闭BGP EVPN路由的VPN-Target过滤功能。

<Sysname> system-view

[Sysname] bgp 100

[Sysname-bgp-default] address-family l2vpn evpn

[Sysname-bgp-default-evpn] undo policy vpn-target


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-1614355209.htm -->

mapping vni命令用来指定本地VXLAN映射的远端VXLAN。

undo mapping vni命令用来恢复缺省情况。

【命令】

mapping vni vxlan-id

undo mapping vni

【缺省情况】

未指定本地VXLAN映射的远端VXLAN。

【视图】

EVPN实例视图

【缺省用户角色】

network-admin

【参数】

vxlan-id：映射的远端VXLAN ID，取值范围为0～16777215。

【使用指导】

在不同的数据中心中，同一租户的相同子网可能使用不同的VXLAN。这些数据中心互联时，若要保证同一租户相同子网之间的流量进行二层转发，则ED设备上需要执行本命令，在不同的VXLAN之间建立映射关系。

可以通过以下方式建立映射关系：

· 将本地VXLAN直接映射为另一个数据中心中使用的VXLAN。采用此方式时，只需在一个数据中心的ED上指定映射的远端VXLAN。例如，数据中心1内使用VXLAN 10、数据中心2内使用VXLAN 20时，只需在数据中心1的ED上配置VXLAN 10映射为远端VXLAN 20。

· 将不同数据中心ED上的本地VXLAN映射为相同的VXLAN（称为中间VXLAN)。采用此方式时，需要在所有数据中心的ED上都指定映射的远端VXLAN为中间VXLAN。例如，数据中心1内使用VXLAN 10、数据中心2内使用VXLAN 20、数据中心3内使用VXLAN 30时，需要在三个数据中心的ED上均配置映射的远端VXLAN为中间VXLAN（如VXLAN 500）。当多个数据中心互联，且不同数据中心使用的VXLAN各不相同时，需要使用此方式。

需要注意的是，本地设备上需要创建映射的远端VXLAN，为其配置EVPN实例，并为该EVPN实例配置RD和Route Target属性。

【举例】

\# 配置本地VXLAN 100映射为远端VXLAN 200。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] vxlan 100

[Sysname-vsi-aaa-vxlan-100] quit

[Sysname-vsi-aaa] evpn encapsulation vxlan

[Sysname-vsi-aaa-evpn-vxlan] mapping vni 200


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-1620460403.htm -->

peer router-mac-local命令用来配置向对等体/对等体组发布路由、将从对等体/对等体组接收到的路由发布给其他对等体时，将路由的Router MAC修改为自身的Router MAC地址。

undo peer router-mac-local命令用来取消该配置。

【命令】

peer { group-name | ipv4-address [ mask-length ] } router-mac-local

undo peer { group-name | ipv4-address [ mask-length ] } router-mac-local

【缺省情况】

不会修改路由的Router MAC。

【视图】

BGP EVPN地址族视图

【缺省用户角色】

network-admin

【参数】

group-name：对等体组的名称，为1～47个字符的字符串，区分大小写。指定的对等体组必须已经创建。

ipv4-address：对等体的IPv4地址。指定的对等体必须已经创建。

mask-length：网络掩码，取值范围为0～32。如果指定本参数，则表示指定网段内的动态对等体。

【使用指导】

数据中心网络的ED设备上需要执行本命令，以便该设备将从数据中心内的对等体/对等体组学到的路由通告给其他数据中心网络的ED设备，或将从其他数据中心网络的ED设备学到的路由通告给数据中心内的对等体/对等体组时，将路由的Router MAC修改为本地的Router MAC。

【举例】

\# 在BGP EVPN地址族视图下，配置向对等体1.1.1.1发布路由、将从对等体1.1.1.1接收到的路由发布给其他对等体时，将路由的Router MAC修改为自身的Router MAC。

<Sysname> system-view

[Sysname] bgp 100

[Sysname-bgp-default] address-family l2vpn evpn

[Sysname-bgp-default-evpn] peer 1.1.1.1 router-mac-local


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-1622773515.htm -->

display evpn route arp suppression命令用来显示EVPN的ARP泛洪抑制信息。

【命令】

display evpn route arp suppression [ local | remote ] [ vsi vsi-name ] [ count ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

local：显示本地ARP泛洪抑制信息。

remote：显示远端ARP泛洪抑制信息。

vsi vsi-name：显示指定VSI的ARP泛洪抑制信息。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示所有VSI的ARP泛洪抑制信息。

count：显示ARP泛洪抑制表项的数目。如果不指定本参数，则显示ARP泛洪抑制表项的具体信息。

【使用指导】

执行本命令时，如果没有指定local和remote参数，则显示EVPN的本地和远端的ARP泛洪抑制信息。

【举例】

\# 显示所有EVPN的ARP泛洪抑制信息。

<Sysname> display evpn route arp suppression

Flags: D - Dynamic B - BGP G - Gateway L - Local active M - Mapping

VSI name: vpna

IP address MAC address Flags

10.1.1.12 0002-0002-0002 B

\# 显示EVPN的ARP泛洪抑制表项总数。

<Sysname> display evpn route arp suppression count

Total number of entries: 1

表1-11 display evpn route arp suppression命令显示信息描述表

| Total number of entries | ARP泛洪抑制表项的总数 |
| --- | --- |


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-341324259.htm -->

ip public-instance命令用来创建公网实例，并进入公网实例视图。如果公网实例已经存在，则直接进入公网实例视图。

undo ip public-instance命令用来删除公网实例。

【命令】

ip public-instance

undo ip public-instance

【缺省情况】

不存在公网实例。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

公网实例用来实现分布式EVPN网关转发公网的三层流量及公私网互通。公网实例可以看作是特殊的VPN实例，分布式EVPN网关对公网实例的处理与VPN实例完全相同。

【举例】

\# 创建公网实例，并进入公网实例视图。

<Sysname> system-view

[Sysname] ip public-instance

[Sysname-public-instance]


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-419567119.htm -->

route-distinguisher命令用来配置EVPN实例的RD（Route Distinguisher，路由标识符）。

undo route-distinguisher命令用来恢复缺省情况。

【命令】

route-distinguisher { route-distinguisher | auto }

undo route-distinguisher

【缺省情况】

未指定EVPN实例的RD。

【视图】

EVPN实例视图

【缺省用户角色】

network-admin

【参数】

route-distinguisher：路由标识符，为3～21个字符的字符串（不允许为全0）。路由标识符有三种格式：

· 16位自治系统号:32位用户自定义数，例如：101:3。

· 32位IP地址:16位用户自定义数，例如：192.168.122.15:1。

· 32位自治系统号:16位用户自定义数字，其中的自治系统号最小值为65536。例如：65536:1

auto：表示自动生成RD。自动生成的RD取值为“N:VXLAN ID”，N为从1开始的整数；如果“N:VXLAN索引”已被使用，则RD取值改为“(N+1):VXLAN ID”，如此反复，直到找到未被使用的RD。

【使用指导】

EVPN采用MP-BGP协议进行邻居自动发现、MAC地址通告、主机路由通告。本命令指定的RD，携带在MP-BGP协议发布的邻居、MAC地址、主机路由信息中，以标识不同EVPN实例的邻居、MAC地址、主机路由信息。

【举例】

\# 配置EVPN的RD为22:1。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] evpn encapsulation vxlan

[Sysname-vsi-aaa-evpn-vxlan] route-distinguisher 22:1


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-575751716.htm -->

route-distinguisher命令用来配置公网实例的RD。

undo route-distinguisher命令用来恢复缺省情况。

【命令】

route-distinguisher route-distinguisher

undo route-distinguisher

【缺省情况】

未配置公网实例的RD。

【视图】

公网实例视图

【缺省用户角色】

network-admin

【参数】

route-distinguisher：路由标识符，为3～21个字符的字符串。路由标识符有三种格式：

· 16位自治系统号:32位用户自定义数，例如：101:3。

· 32位IP地址:16位用户自定义数，例如：192.168.122.15:1。

· 32位自治系统号：16位用户自定义数字，其中的自治系统号最小值为65536。例如：65536:1。

【使用指导】

不能通过重复执行route-distinguisher命令修改公网实例的RD值。如需修改公网实例的RD值，请先通过undo route-distinguisher命令删除公网实例的RD值，再执行route-distinguisher命令配置新的RD值。

【举例】

\# 配置公网实例的RD为22:1。

<Sysname> system-view

[Sysname] ip public-instance

[Sysname-public-instance] route-distinguisher 22:1


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-722426100.htm -->

l3-vni命令用来配置L3VPN的VXLAN ID。

undo l3-vni用来取消配置的L3VPN VXLAN ID。

【命令】

l3-vni vxlan-id

undo l3-vni

【缺省情况】

未配置L3VPN的VXLAN ID。

【视图】

VSI虚接口视图

公网实例视图

【缺省用户角色】

network-admin

【参数】

vxlan-id：VXLAN ID，取值范围为0～16777215。

【使用指导】

分布式网关组网中，需要在网关上配置L3VNI。在网关之间通过VXLAN隧道转发流量时，属于同一路由域、能够进行三层互通的流量通过L3VNI来标识。

转发某个VPN的三层流量时，需要在与该VPN实例关联的VSI虚接口视图下执行本命令；转发公网的三层流量时，不仅需要在属于公网的VSI虚接口视图下执行本命令，还需要在公网实例视图下执行本命令配置与VSI虚接口相同的L3VNI。

【举例】

\# 配置L3VPN的VXLAN ID为1000。

<Sysname> system-view

[Sysname] interface vsi-interface 100

[Sysname-Vsi-interface100] l3-vni 1000


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-742184249.htm -->

address-family evpn命令用来进入公网实例EVPN视图。

undo address-family evpn命令用来删除公网实例EVPN视图下的所有配置。

【命令】

address-family evpn

undo address-family evpn

【视图】

公网实例视图

【缺省用户角色】

network-admin

【使用指导】

在公网实例EVPN视图下可以配置EVPN的参数，如EVPN的RT属性等。

【举例】

\# 进入公网实例EVPN视图。

<Sysname> system-view

[Sysname] ip public-instance

[Sysname-public-instance] address-family evpn

[Sysname-public-instance-evpn]


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-81343308.htm -->

import route-policy命令用来在VPN实例下配置EVPN的入方向路由策略。

undo import route-policy命令用来恢复缺省情况。

【命令】

import route-policy route-policy

undo import route-policy

【缺省情况】

在VPN实例下未配置EVPN的入方向路由策略，即如果接收到的路由携带的Route Target属性中存在与本地配置的Import Target相同的值，则接收该路由。

【视图】

VPN实例EVPN视图

【缺省用户角色】

network-admin

【参数】

route-policy：入方向路由策略名称，为1～63个字符的字符串，区分大小写。

【使用指导】

如果在设备上通过本命令指定了EVPN的入方向路由策略，则EVPN在接收路由时，将利用指定的路由策略对接收的路由进行过滤、改变接收路由的属性等。使用本命令可以更加精确、灵活地控制路由的接收。

多次执行本命令，最后一次执行的命令生效。

VPN实例视图和VPN实例EVPN视图下配置的入方向路由策略均能用于EVPN路由。如果同时配置二者，则EVPN采用VPN实例EVPN视图下的配置。

【举例】

\# 在VPN实例vpn1下配置EVPN的入方向路由策略为poly-1。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] address-family evpn

[Sysname-vpn-evpn-vpn1] import route-policy poly-1

【相关命令】

· route-policy（三层技术-IP路由命令参考/路由策略）


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_-848722157.htm -->

display bgp l2vpn evpn命令用来显示BGP EVPN路由信息。

【命令】

display bgp [ instance instance-name ] l2vpn evpn [ peer ipv4-address { advertised-routes | received-routes } [ statistics ] | route-distinguisher route-distinguisher [ route-type { auto-discovery | es | imet | ip-prefix | mac-ip } ] [ evpn-route route-length [ advertise-info ] ] | route-type { auto-discovery | es | imet | ip-prefix | mac-ip } | statistics ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

instance instance-name：显示指定BGP实例的信息。instance-name表示BGP实例的名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示default实例的信息。

peer ipv4-address：显示向指定对等体发布或者从指定对等体收到的BGP EVPN路由。ipv4-address表示对等体的IP地址。

advertised-routes：显示向指定对等体发布的BGP EVPN路由信息。

received-routes：显示从指定对等体接收到的BGP EVPN路由信息。

statistics：显示BGP EVPN路由的统计信息。

route-distinguisher route-distinguisher：显示指定路由标识符的BGP EVPN路由信息。route-distinguisher为路由标识符，为3～21个字符的字符串。路由标识符有三种格式：

· 16位自治系统号:32位用户自定义数，例如：101:3。

· 32位IP地址:16位用户自定义数，例如：192.168.122.15:1。

· 32位自治系统号:16位用户自定义数字，其中的自治系统号最小值为65536。例如：65536:1。

route-type：显示指定类型的BGP EVPN路由。

auto-discovery：显示以太网自动发现路由（Ethernet auto-discovery route）。

es：显示以太网段路由（Ethernet segment route）。

imet：显示包含性组播以太网标签路由（Inclusive multicast Ethernet tag route），

ip-prefix：显示IP前缀路由（IP prefix advertisement route）。

mac-ip：显示MAC/IP发布路由（MAC/IP advertisement route）。

evpn-route：显示指定BGP EVPN路由的详细信息。evpn-route表示EVPN路由信息，为1～512个字符的字符串，不区分大小写。

route-length：BGP EVPN路由信息的长度，取值范围为0～65535，单位为比特。

advertise-info：显示BGP EVPN路由的通告信息。

【使用指导】

如果未指定任何参数，则显示所有BGP EVPN路由的简要信息。

【举例】

\# 显示所有BGP EVPN路由的简要信息。

<Sysname> display bgp l2vpn evpn

 BGP local router ID is 1.1.1.9

 Status codes: * - valid, > - best, d - dampened, h - history,

 s - suppressed, S - stale, i - internal, e - external

 Origin: i - IGP, e - EGP,? - incomplete

 Total number of routes from all PEs: 6

 Route distinguisher: 100:1

 Total number of routes: 3

 Network NextHop MED LocPrf PrefVal Path/Ogn

* > [2][0][48][00aa.00bb.00cc][4][0.0.0.0]/136

 10.1.1.2 0 32768?

* e 10.1.1.1 0 0 65410?

* > [3][300][16][::ffff:1.1.1.1]/176

 127.0.0.1 0 32768?

 Route distinguisher: 200:1

 Total number of routes: 2

 Network NextHop MED LocPrf PrefVal Path/Ogn

* >i [2][0][48][00aa.00cc.00dd][4][1.1.1.1]/136

 3.3.3.9 0 100 0?

* >i [3][300][16][::ffff:2.2.2.2]/176

 3.3.3.9 0 100 0 65420?

Route distinguisher of public instance: 1:15

Total number of routes: 1

 Network NextHop MED LocPrf PrefVal Path/Ogn

* >e [2][0][48][0011.0022.0033][32][11.22.33.55]/136

 30.30.1.2 0 0 100i

表1-1 display bgp l2vpn evpn命令简要显示信息描述表

| | | | |
| --- | --- | --- | --- |

\# 显示路由标识符为1.1.1.1:100的BGP EVPN路由[1][00:01:02:03:04:05:06:07:08:09][5]/120的详细信息。

<Sysname> display bgp l2vpn evpn route-distinguisher 1.1.1.1:100 [1][00:01:02:03:04:05:06:07:08:09][5] 120

 BGP local router ID: 172.16.250.133

 Local AS number: 100

 Route distinguisher: 1.1.1.1:100

 Total number of routes: 1

 Paths: 1 available, 1 best

 BGP routing table information of [1][00:01:02:03:04:05:06:07:08:09][5]/120:

 From: 10.1.1.2 (192.168.56.17)

 Rely nexthop: 10.1.1.2

 Original nexthop: 10.1.1.2

 OutLabel: 0

 Ext-Community: <RT: 1:2>, <Encapsulation Type: VXLAN >, <ESI Label: Flag 0,

 Label 1>

 AS-path: 200

 Origin: igp

 Attribute value: MED 0, pref-val 0

 State: valid, external, best

 IP precedence: N/A

 QoS local ID: N/A

 Traffic index: N/A

 EVPN route type: Ethernet auto-discovery route

 ESI: 00:01:02:03:04:05:06:07:08:09

 Ethernet tag ID: 5

 MPLS label: 10

表1-2 display bgp l2vpn evpn命令中Ethernet auto-discovery route详细显示信息描述表

| MPLS label | MPLS标签，目前此字段无意义 |
| --- | --- |

\# 显示路由标识符为1.1.1.1:100的BGP EVPN路由[2][5][48][0001-0203-0405][32][4.5.5.5]/136的详细信息。

<Sysname> display bgp l2vpn evpn route-distinguisher 1.1.1.1:100 [2][5][48][0001-0203-0405][32][5.5.5.5] 136

 BGP local router ID: 172.16.250.133

 Local AS number: 100

 Route distinguisher: 1.1.1.1:100

 Total number of routes: 1

 Paths: 1 available, 1 best

 BGP routing table information of [2][5][48][0001-0203-0405][32][5.5.5.5]/136:

 From: 10.1.1.2 (192.168.56.17)

 Rely nexthop: 10.1.1.2

 Original nexthop: 10.1.1.2

 OutLabel: 0

 Ext-Community: <RT: 1:2>, <RT: 1:3>, <RT: 1:4>, <RT: 1:5>, <RT: 1:6>, <RT: 1:7

 >, <Encapsulation Type: VXLAN>, <Router's Mac: 0006-0708-0910

 >, <MAC Mobility: Flag 0, SeqNum 2>, <Default GateWay>

 AS-path: 200

 Origin: igp

 Attribute value: MED 0, pref-val 0

 State: valid, external, best

 IP precedence: N/A

 QoS local ID: N/A

 Traffic index: N/A

 EVPN route type: MAC/IP advertisement route

 ESI: 00:01:02:03:04:05:06:07:08:09

 Ethernet tag ID: 5

 MAC address: 0001-0203-0405

 IP address: 5.5.5.5/32

 MPLS label1: 10

 MPLS label2: 0

表1-3 display bgp l2vpn evpn命令中MAC/IP advertisement route详细显示信息描述表

| MPLS label2 | 用于三层转发的VXLAN ID，即L3VNI |
| --- | --- |

\# 显示路由标识符为1.1.1.1:100的BGP EVPN路由[3][0][32][5.5.5.5]/80的详细信息。

<Sysname> display bgp l2vpn evpn route-distinguisher 1.1.1.1:100 [3][0][32][4.5.5.5] 80

BGP local router ID: 172.16.250.133

 Local AS number: 100

 Route distinguisher: 1.1.1.1:100

 Total number of routes: 1

 Paths: 1 available, 1 best

 BGP routing table information of [3][0][32][4.5.5.5]/80:

 From: 10.1.1.2 (192.168.56.17)

 Rely nexthop: 10.1.1.2

 Original nexthop: 10.1.1.2

 OutLabel: 0

 Ext-Community: <RT: 1:2>, <Encapsulation Type: VXLAN>

 AS-path: 200

 Origin: igp

 Attribute value: MED 0,pref-val 0

 State: valid, external, best

 IP precedence: N/A

 QoS local ID: N/A

 Traffic index: N/A

 EVPN route type: Inclusive multicast Ethernet tag route

 Ethernet tag ID: 0

 Origin address: 5.5.5.5/32

表1-4 display bgp l2vpn evpn命令中Inclusive multicast Ethernet tag route详细显示信息描述表

| Origin address | 始发路由器地址 |
| --- | --- |

\# 显示路由标识符为1.1.1.1:100的EVPN路由[4][00:00:00:00:00:00:00:00:00:0a][32][4.5.5.5]/128的详细信息。

<Sysname> display bgp l2vpn evpn route-distinguisher 1.1.1.1:100 [4][00:00:00:00:00:00:00:00:00:0a][32][4.5.5.5] 128

 BGP local router ID: 172.16.250.133

 Local AS number: 100

 Route distinguisher: 1.1.1.1:100

 Total number of routes: 1

 Paths: 1 available, 1 best

 BGP routing table information of [4][00:00:00:00:00:00:00:00:00:0a][32] [4.5.5

.5]/128:

 From: 10.1.1.2 (192.168.56.17)

 Rely nexthop: 10.1.1.2

 Original nexthop: 10.1.1.2

 OutLabel: 0

 Ext-Community: <RT: 1:2>, <Encapsulation Type: VXLAN>, <ES-Import RT: 1:1>

 AS-path: 200

 Origin: igp

 Attribute value: MED 0,pref-val 0

 State: valid, external, best

 IP precedence: N/A

 QoS local ID: N/A

 Traffic index: N/A

 EVPN route type: Ethernet segment route

 ESI: 00:00:00:00:00:00:00:00:00:0a

 Origin address: 4.5.5.5/32

表1-5 display bgp l2vpn evpn命令中Ethernet segment route详细显示信息描述表

| Origin address | 始发路由器地址 |
| --- | --- |

\# 显示路由标识符为1.1.1.1:100的BGP EVPN路由[5][10][32][4.5.5.5]/80的详细信息。

<Sysname> display bgp l2vpn evpn route-distinguisher 1.1.1.1:100 [5][10][32][4.5.5.5] 80

 BGP local router ID: 172.16.250.133

 Local AS number: 100

 Route distinguisher: 1.1.1.1:100

 Total number of routes: 1

 Paths: 1 available, 1 best

 BGP routing table information of [5][10][32][4.5.5.5]/80:

 From: 10.1.1.2 (192.168.56.17)

 Rely nexthop: 10.1.1.2

 Original nexthop: 10.1.1.2

 OutLabel: 0

 Ext-Community: <RT: 1:2>, <Encapsulation Type: VXLAN>, <Router's Mac:

 0006-0708-0910>

 AS-path: 200

 Origin: igp

 Attribute value: MED 0,pref-val 0

 State: valid, external, best

 IP precedence: N/A

 QoS local ID: N/A

 Traffic index: N/A

 EVPN route type: IP prefix advertisement route

 ESI: 00:00:00:00:00:00:00:00:00:0a

 Ethernet tag ID: 10

 IP address: 4.5.5.5/32

 Gateway address: 0.0.0.0

 MPLS Label: 1

表1-6 display bgp l2vpn evpn命令中IP prefix advertisement route详细显示信息描述表

| MPLS Label | 用于三层转发的VXLAN ID，即L3VNI |
| --- | --- |

\# 显示路由标识符为1.1.1.1:100的EVPN路由[4][00:00:00:00:00:00:00:00:00:0a][32][4.5.5.5]/128的通告信息。

<Sysname> display bgp l2vpn evpn route-distinguisher 1.1.1.1:100 [4][00:00:00:00:00:00:00:00:00:0a] [32][4.5.5.5] 128 advertise-info

 BGP local router ID: 172.16.250.133

 Local AS number: 100

 Route distinguisher: 1.1.1.1:100

 Total number of routes: 1

 Paths: 1 best

 BGP routing table information of [4][00:00:00:00:00:00:00:00:00:0a][32][4.5.5.5]/128:

 Advertised to peers (1 in total):

 10.2.1.2

表1-7 display bgp l2vpn evpn advertise-info命令显示信息描述表

| Advertised to peers (1 in total) | 该路由已经向哪些BGP EVPN对等体发送，以及对等体的数目 |
| --- | --- |


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1183658096.htm -->

evpn encapsulation命令用来创建EVPN实例，并进入EVPN实例视图。如果EVPN实例已经存在，则直接进入EVPN实例视图。

undo evpn encapsulation命令用来恢复缺省情况。

【命令】

evpn encapsulation vxlan

undo evpn encapsulation

【缺省情况】

不存在EVPN实例。

【视图】

VSI视图

【缺省用户角色】

network-admin

【参数】

vxlan：表示EVPN采用VXLAN封装方式。

【使用指导】

只有创建EVPN实例后，才能进行EVPN相关配置。

【举例】

\# 创建EVPN实例，并进入EVPN实例视图。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] evpn encapsulation vxlan

[Sysname-vsi-aaa-evpn-vxlan]


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1277734500.htm -->

display evpn route arp命令用来显示EVPN的ARP信息。

【命令】

display evpn route arp [ local | remote ] [ public-instance | vpn-instance vpn-instance-name ] [ count ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

local：显示本地ARP信息。

remote：显示远端ARP信息。

public-instance：显示公网实例的ARP信息。

vpn-instance vpn-instance-name：显示指定VPN实例的ARP信息。vpn-instance-name表示 MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写。

count：显示ARP表项的数目。如果不指定本参数，则显示ARP表项的具体信息。

【使用指导】

执行本命令时，如果没有指定local和remote参数，则显示EVPN的本地和远端ARP信息。

执行本命令时，如果没有指定public-instance和vpn-instance vpn-instance-name参数，则显示公网实例和所有VPN实例的ARP信息。

【举例】

\# 显示所有EVPN的ARP信息。

<Sysname> display evpn route arp

Flags: D - Dynamic B - BGP G - Gateway L - Local active M - Mapping

Interface: Vsi-interface1 VPN instance name: vpna

IP address MAC address Router MAC VSI Index Flags

10.1.1.1 0003-0003-0003 a0ce-7e40-0400 0 GL

10.1.1.11 0001-0001-0001 a0ce-7e40-0400 0 DL

Interface: Vsi-interface2 Public instance

IP address MAC address Router MAC VSI index Flags

11.1.1.1 0004-0004-0004 a0ce-7e40-0400 0 GL

11.1.1.11 0002-0002-0002 a0ce-7e40-0400 0 DL

\# 显示EVPN的ARP表项总数。

<Sysname> display evpn route arp count

Total number of entries: 4

表1-10 display evpn route arp命令显示信息描述表

| Total number of entries | ARP表项的总数 |
| --- | --- |


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1277972008.htm -->

dci enable命令用来在接口上开启DCI功能。

undo dci enable命令用来关闭接口的DCI功能。

【命令】

dci enable

undo dci enable

【缺省情况】

接口上DCI功能处于关闭状态。

【视图】

接口视图

【缺省用户角色】

network-admin

【使用指导】

EVPN数据中心互联组网中，需要在ED间互连的三层接口上开启DCI功能。

在主接口上开启DCI功能后，子接口会继承主接口的配置。

【举例】

\# 在VLAN接口2上开启DCI功能。

<Sysname> system-view

[Sysname] interface vlan-interface 2

[Sysname-Vlan-interface2] dci enable


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1465347446.htm -->

address-family l2vpn evpn命令用来创建BGP EVPN地址族，并进入BGP EVPN地址族视图。如果BGP EVPN地址族已经存在，直接进入BGP EVPN地址族视图。

undo address-family l2vpn evpn命令用来删除BGP EVPN地址族，及相应地址族视图下的所有配置。

【命令】

address-family l2vpn evpn

undo address-family l2vpn evpn

【缺省情况】

不存在BGP EVPN地址族。

【视图】

BGP实例视图

【缺省用户角色】

network-admin

【使用指导】

BGP EVPN地址族视图下的配置，只对公网BGP EVPN地址族的路由和对等体生效。

【举例】

\# 创建BGP EVPN地址族，并进入BGP EVPN地址族视图。

<Sysname> system-view

[Sysname] bgp 100

[Sysname-bgp-default] address-family l2vpn evpn

[Sysname-bgp-default-evpn]


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1533775175.htm -->

rr-filter命令用来配置路由反射器对反射的EVPN路由进行过滤。

undo rr-filter命令用来恢复缺省情况。

【命令】

rr-filter ext-comm-list-number

undo rr-filter

【缺省情况】

路由反射器不会对反射的EVPN路由进行过滤。

【视图】

BGP EVPN地址族视图

【缺省用户角色】

network-admin

【参数】

ext-comm-list-number：扩展团体属性列表号，取值范围为1～199。

【使用指导】

执行本命令后，路由反射器将根据扩展团体属性列表对接收的EVPN路由进行过滤：只有接收的BGP EVPN路由通过扩展团体属性列表过滤时，路由反射器才会反射该EVPN路由。

当一个集群中存在多个路由反射器时，通过在不同的路由反射器上配置不同的反射策略，可以实现路由反射器之间的负载分担。

扩展团体属性列表的详细介绍，请参见“三层技术-IP路由配置指导”中的“路由策略”。

【举例】

\# 配置路由反射器只反射通过扩展团体属性列表10过滤的BGP EVPN路由。

<Sysname> system-view

[Sysname] bgp 100

[Sysname-bgp-default] address-family l2vpn evpn

[Sysname-bgp-default-evpn] rr-filter 10

【相关命令】

· ip extcommunity-list（三层技术-IP路由命令参考/路由策略）


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1791516678.htm -->

display evpn auto-discovery命令用来显示EVPN通过BGP自动发现的邻居信息。

【命令】

display evpn auto-discovery { imet [ peer ip-address] [ vsi vsi-name ] | macip-prefix [ nexthop next-hop ] [ count ] }

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

imet：显示通过包含性组播以太网标签路由（Inclusive multicast Ethernet tag route）发现的邻居信息。

peer ip-address：显示指定邻居的自动发现相关信息。ip-address为邻居的IP地址。如果未指定本参数，则显示自动发现的所有邻居的信息。

vsi vsi-name：显示指定VSI内自动发现的邻居信息。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示所有VSI内自动发现的邻居信息。

macip-prefix：显示通过MAC/IP发布路由和IP前缀路由发现的邻居信息。

nexthop next-hop：显示从指定路由下一跳学习到的邻居信息。如果未指定本参数，则显示从所有路由下一跳学习到的邻居信息。

count：显示自动发现的邻居数目。如果未指定本参数，则显示邻居的具体信息。

【举例】

\# 显示通过包含性组播以太网标签路由发现的邻居信息。

<Sysname> display evpn auto-discovery imet

Total number of automatically discovered peers: 2

VSI name: vpna

RD PE_address Tunnel_address Tunnel mode VXLAN ID

1:10 2.2.2.2 2.2.2.2 VXLAN 10

2:100 3.3.3.3 3.3.3.3 VXLAN 10

表1-8 display evpn auto-discovery imet命令显示信息描述表

| VXLAN ID | VXLAN编号 |
| --- | --- |

\# 显示通过MAC/IP发布路由和IP前缀路由发现的邻居信息。

<Sysname> display evpn auto-discovery macip-prefix

Destination IP Source IP L3VNI Tunnel mode Outgoing interface

1.1.1.1 3.3.3.3 200 VXLAN Vsi-interface3

2.2.2.2 3.3.3.3 200 VXLAN Vsi-interface3

\# 显示通过MAC/IP发布路由和IP前缀路由发现的邻居总数。

<Sysname> display evpn auto-discovery macip-prefix count

Total number of entries: 2

表1-9 display evpn auto-discovery macip-prefix命令显示信息描述表

| Total number of entries | 邻接表项的总数 |
| --- | --- |


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_185824155.htm -->

peer next-hop-invariable命令用来配置向EBGP对等体/对等体组发布路由时不改变下一跳。

undo peer next-hop-invariable命令用来配置向EBGP对等体/对等体组发布路由时会将下一跳改为自己的地址。

【命令】

peer { group-name | ipv4-address [ mask-length ] } next-hop-invariable

undo peer { group-name | ipv4-address [ mask-length ] } next-hop-invariable

【缺省情况】

向EBGP对等体/对等体组发布路由时会将下一跳改为自己的地址。

【视图】

BGP EVPN地址族视图

【缺省用户角色】

network-admin

【参数】

group-name：对等体组的名称，为1～47个字符的字符串，区分大小写。

ipv4-address：对等体的IPv4地址。

mask-length：网络掩码，取值范围为0～32。如果指定本参数，则表示指定网段内的动态对等体。

【使用指导】

在两个数据中心之间，BGP EVPN路由通过IBGP—EBGP—IBGP的路径发布。不同数据中心的两个主机通信时，报文通过入口VTEP和出口VTEP之间的VXLAN隧道传输。因此，需要执行本命令配置IBGP路由通告给EBGP对等体时不改变下一跳地址，使得VTEP学习到的BGP EVPN路由下一跳为远端VTEP的地址，以便在两个VTEP之间建立VXLAN隧道。

本命令与peer next-hop-local命令互斥。

【举例】

\# 配置向EBGP对等体1.1.1.1发布路由时不改变下一跳。

<Sysname> system-view

[Sysname] bgp 100

[Sysname-bgp-default] address-family l2vpn evpn

[Sysname-bgp-default-evpn] peer 1.1.1.1 next-hop-invariable

【相关命令】

· peer next-hop-local（三层技术-IP路由命令参考/BGP）


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1881412085.htm -->

address-family ipv4命令用来进入公网实例IPv4 VPN视图。

undo address-family ipv4命令用来删除公网实例IPv4 VPN视图下的所有配置。

【命令】

address-family ipv4

undo address-family ipv4

【视图】

公网实例视图

【缺省用户角色】

network-admin

【举例】

\# 进入公网实例IPv4 VPN视图。

<Sysname> system-view

[Sysname] ip public-instance

[Sysname-public-instance] address-family ipv4

[Sysname-public-instance-ipv4]


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_1988187603.htm -->

display evpn routing-table命令用来显示EVPN的路由表信息。

【命令】

display evpn routing-table { public-instance | vpn-instance vpn-instance-name } [ count ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

public-instance：显示公网实例的路由信息。

vpn-instance vpn-instance-name：显示指定VPN实例的路由信息。vpn-instance-name表示MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写。

count：显示路由表项的数目。如果不指定本参数，则显示路由表项的具体信息。

【举例】

\# 显示VPN实例对应的EVPN的路由信息。

<Sysname> display evpn routing-table vpn-instance vpn1

VPN instance name: vpn1 Local L3VNI: 7

IP address Nexthop Outgoing interface NibID

10.1.1.11 1.1.1.1 Vsi-interface3 0x18000000

10.1.1.12 2.2.2.2 Vsi-interface3 0x18000001

\# 显示公网实例的EVPN路由信息。

<Sysname> display evpn routing-table public-instance

Public instance Local L3VNI: 3900

IP address Nexthop Outgoing interface NibID

10.1.1.11 1.1.1.1 Vsi-interface3 0x18000000

10.1.1.12 2.2.2.2 Vsi-interface3 0x18000001

\# 显示VPN实例对应的EVPN路由表项总数。

<Sysname> display evpn routing-table vpn-instance vpn1 count

Total number of entries: 2

表1-13 display evpn routing-table命令显示信息描述表

| Total number of entries | 路由表项的总数 |
| --- | --- |


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_2070316454.htm -->

vpn-target命令用来配置EVPN的Route Target属性。

undo vpn-target命令用来删除指定的Route Target属性。

【命令】

EVPN实例视图：

vpn-target { vpn-target&<1-8> | auto } [ both | export-extcommunity | import-extcommunity ]

undo vpn-target { vpn-target&<1-8> | auto | all } [ both | export-extcommunity | import-extcommunity ]

VPN实例EVPN视图/公网实例IPv4 VPN视图/公网实例EVPN视图：

vpn-target vpn-target&<1-8> [ both | export-extcommunity | import-extcommunity ]

undo vpn-target { all | vpn-target&<1-8> [ both | export-extcommunity | import-extcommunity ] }

【缺省情况】

未指定EVPN的Route Target属性。

【视图】

EVPN实例视图

VPN实例EVPN视图

公网实例IPv4 VPN视图

公网实例EVPN视图

【缺省用户角色】

network-admin

【参数】

vpn-target&<1-8>：Route Target属性值，vpn-target为3～21个字符的字符串。&<1-8>表示前面的参数最多可以输入8次。Route Target有三种格式：

· 16位自治系统号:32位用户自定义数，例如：101:3。

· 32位IP地址:16位用户自定义数，例如：192.168.122.15:1。

· 32位自治系统号:16位用户自定义数字，其中的自治系统号最小值为65536。例如：65536:1。

auto：表示自动生成RT。自动生成的RT取值为“BGP AS:VXLAN ID”。

both：指定配置的Route Target值同时作为Import Target和Export Target。没有指定both、export-extcommunity和import-extcommunity中的任何一个参数时，缺省值为both。

export-extcommunity：指定配置的Route Target值为Export Target。

import-extcommunity：指定配置的Route Target值为Import Target。

all：所有Route Target值。

【使用指导】

EVPN采用MP-BGP协议进行邻居自动发现、MAC地址通告、主机路由通告等。本地设备在通过MP-BGP的Update消息将BGP EVPN路由发送给远端设备时，将Update消息中携带的VPN target属性设置为Export target。远端设备接收到BGP EVPN路由后，将该路由中携带的Export Target属性与本地配置的Import Target进行比较，如果二者中存在相同的值，则接收该信息。

【举例】

\# 配置EVPN的Import Target为10:1、100:1和1000:1。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] evpn encapsulation vxlan

[Sysname-vsi-aaa-evpn-vxlan] vpn-target 10:1 100:1 1000:1 import-extcommunity


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_2135640747.htm -->

display evpn route mac命令用来显示EVPN的MAC地址信息。

【命令】

display evpn route mac [ local | remote ] [ vsi vsi-name ] [ count ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

local：显示本地MAC地址信息。

remote：显示远端MAC地址信息。

vsi vsi-name：显示指定VSI的MAC地址信息。vsi-name表示VSI的名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示所有VSI的MAC地址信息。

count：显示MAC地址表项的数目。如果不指定本参数，则显示MAC地址的具体信息。

【使用指导】

执行本命令时，如果没有指定local和remote参数，则显示EVPN的本地和远端MAC地址信息。

【举例】

\# 显示所有EVPN的本地和远端MAC地址信息。

<Sysname> display evpn route mac

Flags: D - Dynamic B - BGP G - Gateway L - Local active M - Mapping

VSI name: bbb

MAC address Link ID/Name Flags Next hop

0000-0000-000a 1 DB -

0000-0000-0009 Tunnel1 B 2.2.2.2

\# 显示EVPN的MAC地址表项数目。

<Sysname> display evpn route mac count

Total number of entries: 2

表1-12 display evpn route mac命令显示信息描述表

| Total number of entries | MAC地址表项的总数 |
| --- | --- |


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_504576312.htm -->

export route-policy命令用来在VPN实例下配置EVPN的出方向路由策略。

undo export route-policy命令用来恢复缺省情况。

【命令】

export route-policy route-policy

undo export route-policy

【缺省情况】

在VPN实例下未配置EVPN的出方向路由策略，即不对发布的路由进行过滤。

【视图】

VPN实例EVPN视图

【缺省用户角色】

network-admin

【参数】

route-policy：出方向路由策略名称，为1～63个字符的字符串，区分大小写。

【使用指导】

如果在设备上通过本命令指定了EVPN的出方向路由策略，则EVPN在发布路由时，将利用指定的路由策略对发布的路由进行过滤、改变发布路由的属性等。使用本命令可以更加精确、灵活地控制路由的发布。

多次执行本命令，最后一次执行的命令生效。

VPN实例视图和VPN实例EVPN视图下配置的出方向路由策略均能用于EVPN路由。如果同时配置二者，则EVPN采用VPN实例EVPN视图下的配置。

【举例】

\# 在VPN实例vpn1下配置EVPN的出方向路由策略为poly-1。

<Sysname> system-view

[Sysname] ip vpn-instance vpn1

[Sysname-vpn-instance-vpn1] address-family evpn

[Sysname-vpn-evpn-vpn1] export route-policy poly-1

【相关命令】

· route-policy（三层技术-IP路由命令参考/路由策略）


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_671475947.htm -->

mac-advertising disable命令用来配置禁止通告MAC地址信息，并撤销已经通告的MAC地址信息。

undo mac-advertising disable命令用来恢复缺省情况。

【命令】

mac-advertising disable

undo mac-advertising disable

【缺省情况】

允许通告MAC地址信息。

【视图】

EVPN实例视图

【缺省用户角色】

network-admin

【使用指导】

VTEP可能会同时向远端VTEP通告MAC地址信息和ARP信息。其中，ARP信息中已经包含MAC地址信息。为了避免重复，可以执行本命令来禁止本端VTEP向远端VTEP通告MAC地址信息。执行本命令后，本端VTEP还会撤销已经发布的MAC地址信息。

【举例】

\# 配置EVPN实例禁止通告MAC地址信息，并撤销已经通告的MAC地址信息。

<Sysname> system-view

[Sysname] vsi aaa

[Sysname-vsi-aaa] evpn encapsulation vxlan

[Sysname-vsi-aaa-evpn-vxlan] mac-advertising disable


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_885604136.htm -->

address-family evpn命令用来进入VPN实例EVPN视图。

undo address-family evpn命令用来删除VPN实例EVPN视图下的所有配置。

【命令】

address-family evpn

undo address-family evpn

【视图】

VPN实例视图

【缺省用户角色】

network-admin

【使用指导】

在VPN实例EVPN视图下可以配置EVPN的参数，如EVPN的RT属性、应用的出方向路由策略等。

【举例】

\# 进入VPN实例EVPN视图。

<Sysname> system-view

[Sysname] ip vpn-instance tenant

[Sysname-vpn-instance-tenant] address-family evpn

[Sysname-vpn-evpn-tenant]


---

<!-- 14-EVPN命令参考/html/-2090487470_201252934_-970606464_999340568.htm -->

advertise l2vpn evpn命令用来配置允许对外发布 BGP EVPN路由。

undo advertise l2vpn evpn命令用来禁止对外发布 BGP EVPN路由。

【命令】

advertise l2vpn evpn

undo advertise l2vpn evpn

【缺省情况】

允许对外发布BGP EVPN路由。

【视图】

BGP-VPN IPv4地址族视图

【缺省用户角色】

network-admin

【使用指导】

配置允许对外发布 BGP EVPN路由后，设备接收到BGP EVPN路由，并将其添加到某个VPN实例路由表后，会将该路由（私网路由）发布到本地站点。

【举例】

\# 配置允许BGP VPN实例vpn1对外发布BGP EVPN路由。

<Sysname> system-view

[Sysname] bgp 100

[Sysname-bgp-default] ip vpn-instance vpn1

[Sysname-bgp-default-vpn1] address-family ipv4

[Sysname-bgp-default-ipv4-vpn1] advertise l2vpn evpn


---

<!-- 14-EVPN命令参考/html/00-前言.htm -->

前 言

本命令参考主要介绍S6800系列以太网交换机的EVPN配置命令。

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
