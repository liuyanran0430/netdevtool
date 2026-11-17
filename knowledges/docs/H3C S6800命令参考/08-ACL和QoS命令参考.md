# 08-ACL和QoS命令参考

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-1192943446.htm -->

step命令用来配置规则编号的步长。

undo step命令用来恢复缺省情况。

【命令】

step step-value [ start start-value ]

undo step

【缺省情况】

规则编号的步长为5，起始值为0。

【视图】

IPv4基本ACL视图/IPv4高级ACL视图

IPv6基本ACL视图/IPv6高级ACL视图

二层ACL视图

【缺省用户角色】

network-admin

【参数】

step-value：表示规则编号的步长值，取值范围为1～20。

start-value：表示规则编号的起始值。取值范围为0～20。

【使用指导】

系统为规则自动分配编号的方式如下：系统从规则编号的起始值开始，自动分配一个大于现有最大编号的步长最小倍数。譬如原有编号为0、5、9、10和12的五条规则，步长为5，此时如果创建一条规则且不指定编号，那么系统将自动为其分配编号15。

如果步长或规则编号的起始值发生了改变，ACL内原有全部规则的编号都将自动从规则编号的起始值开始按步长重新排列。譬如，某ACL内原有编号为0、5、9、10和15的五条规则，当修改步长为2之后，这些规则的编号将依次变为0、2、4、6和8。

【举例】

\# 将IPv4基本ACL 2000的规则编号的步长配置为2。

<Sysname> system-view

[Sysname] acl basic 2000

[Sysname-acl-ipv4-basic-2000] step 2

【相关命令】

· display acl


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-1505995266.htm -->

display packet-filter verbose命令用来显示ACL在报文过滤中的详细应用情况。

【命令】

display packet-filter verbose interface interface-type interface-number { inbound | outbound } [ [ ipv6 | mac | user-defined ] { acl-number | name acl-name } ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface interface-type interface-number：显示指定接口上ACL在报文过滤中的详细应用情况。interface-type interface-number表示接口类型和接口编号。当接口类型为以太网接口时，不需要指定slot参数。

inbound：显示入方向上ACL在报文过滤中的详细应用情况。

outbound：显示出方向上ACL在报文过滤中的详细应用情况。

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：显示指定编号ACL在报文过滤中的详细应用情况。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name acl-name：显示指定名称ACL在报文过滤中的详细应用情况。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

slot slot-number：显示指定成员设备上ACL在报文过滤中的详细应用情况，slot-number表示设备在IRF中的成员编号。若未指定本参数，将显示主用设备上ACL在报文过滤中的详细应用情况。

【使用指导】

若未指定acl-number、name acl-name和ACL类型（ipv6、mac、user-defined）参数，将显示全部IPv4 ACL在报文过滤中的详细应用情况。

如果未指定ipv6、mac或user-defined参数，则表示IPv4 ACL。

【举例】

\# 显示接口Ten-GigabitEthernet1/0/1入方向上全部ACL在报文过滤中的详细应用情况。

<Sysname> display packet-filter verbose interface ten-gigabitethernet 1/0/1 inbound

Interface: Ten-GigabitEthernet1/0/1

 Inbound policy:

 IPv4 ACL 2001

 rule 0 permit

 rule 5 permit source 1.1.1.1 0 (Failed)

 rule 10 permit vpn-instance test (Failed)

 IPv4 ACL 2002 (Failed)

 IPv6 ACL 2000

 rule 0 permit

 MAC ACL 4000

 IPv4 default action: Deny

 IPv6 default action: Deny

 MAC default action: Deny

表1-5 display packet-filter verbose命令显示信息描述表

| MAC default action | 报文过滤的缺省动作，包括： · Deny：报文过滤缺省动作为Deny应用成功 · Deny (Failed)：报文过滤缺省动作为Deny应用失败，实际动作仍为Permit · Permit：报文过滤缺省动作为Permit |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-1564965768.htm -->

rule comment命令用来为规则配置描述信息。

undo rule comment命令用来删除指定规则的描述信息。

【命令】

rule rule-id comment text

undo rule rule-id comment

【缺省情况】

规则没有描述信息。

【视图】

IPv4基本ACL视图/IPv4高级ACL视图

IPv6基本ACL视图/IPv6高级ACL视图

二层ACL视图

用户自定义ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定规则的编号，该规则必须存在。取值范围为0～65534。

text：表示规则的描述信息，为1～127个字符的字符串，区分大小写。

【使用指导】

使用rule comment命令时，如果指定的规则没有描述信息，则为其添加描述信息，否则修改其描述信息。

【举例】

\# 为IPv4基本ACL 2000配置规则0，并为该规则配置描述信息。

<Sysname> system-view

[Sysname] acl basic 2000

[Sysname-acl-ipv4-basic-2000] rule 0 deny source 1.1.1.1 0

[Sysname-acl-ipv4-basic-2000] rule 0 comment This rule is used on ten-gigabitethernet 1/0/1.

【相关命令】

· display acl


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-1794498262.htm -->

acl logging interval命令用来配置报文过滤日志信息的生成与发送周期。

undo acl logging interval命令用来恢复缺省情况。

【命令】

acl logging interval interval

undo acl logging interval

【缺省情况】

报文过滤日志信息的生成与发送周期为0分钟，即不记录报文过滤的日志。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

interval：报文过滤日志信息的生成与发送周期，取值范围为0～1440，且必须为5的整数倍，0表示不进行记录，单位为分钟。

【使用指导】

系统只支持对应用IPv4基本ACL、IPv4高级ACL、IPv6基本ACL或IPv6高级ACL进行报文过滤的报文过滤日志信息进行记录，且在上述ACL中配置规则时必须指定logging参数。

设备周期性地生成报文过滤日志信息并发送到信息中心，包括该周期内被匹配的报文数量以及所使用的ACL规则。同时，还会对匹配规则的数据流的第一个数据包进行记录并送到信息中心。有关信息中心的详细介绍请参见“网络管理和监控配置指导”中的“信息中心”。

【举例】

\# 配置IPv4报文过滤日志的生成与发送周期为10分钟。

<Sysname> system-view

[Sysname] acl logging interval 10

【相关命令】

· rule (IPv4 advanced ACL view)

· rule (IPv4 basic ACL view)

· rule (IPv6 advanced ACL view)

· rule (IPv6 basic ACL view)


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-1878660045.htm -->

rule命令用来为IPv4基本ACL创建一条规则。

undo rule命令用来为IPv4基本ACL删除一条规则或删除规则中的部分内容。

【命令】

rule [ rule-id ] { deny | permit } [ counting | fragment | logging | source { source-address source-wildcard | any } | time-range time-range-name | vpn-instance vpn-instance-name ] *

undo rule rule-id [ counting | fragment | logging | source | time-range | vpn-instance ] *

undo rule { deny | permit } [ counting | fragment | logging | source { source-address source-wildcard | any } | time-range time-range-name | vpn-instance vpn-instance-name ] *

【缺省情况】

IPv4基本ACL内不存在任何规则。

【视图】

IPv4基本ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定IPv4基本ACL规则的编号，取值范围为0～65534。若未指定本参数，系统将从规则编号的起始值开始，自动分配一个大于现有最大编号的步长最小倍数。譬如现有规则的最大编号为28，步长为5，那么自动分配的新编号将是30。

deny：表示拒绝符合条件的报文。

permit：表示允许符合条件的报文。

counting：表示开启规则匹配统计功能，缺省为关闭。

fragment：表示仅对非首片分片报文有效，而对非分片报文和首片分片报文无效。若未指定本参数，表示该规则对非分片报文和分片报文均有效。

logging：表示对符合条件的报文可记录日志信息。该功能需要使用该ACL的模块支持日志记录功能，例如报文过滤。

source { source-address source-wildcard | any }：指定规则的源IP地址信息。source-address表示报文的源IP地址，source-wildcard表示源IP地址的通配符掩码（为0表示主机地址），any表示任意源IP地址。

time-range time-range-name：指定本规则生效的时间段。time-range-name表示时间段的名称，为1～32个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。若该时间段尚未配置，该规则仍会成功创建但系统将给出提示信息，并在该时间段的配置完成后此规则才会生效。有关时间段的详细介绍和具体配置过程，请参见“ACL和QoS配置指导”中的“时间段”。

vpn-instance vpn-instance-name：表示对指定VPN实例中的报文有效。vpn-instance-name表示MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写。若未指定本参数，表示该规则对非VPN报文和VPN报文均有效。

【使用指导】

使用rule命令时，如果指定编号的规则不存在，则创建一条新的规则；如果指定编号的规则已存在，则对旧规则进行修改，即在其原有内容的基础上叠加新的内容。

新创建或修改的规则不能与已有规则的内容完全相同，否则将提示出错，并导致该操作失败。

当ACL的规则匹配顺序为配置顺序时，允许修改该ACL内的任意一条已有规则；当ACL的规则匹配顺序为自动排序时，不允许修改该ACL内的已有规则，否则将提示出错。

在VXLAN组网中，当IPv4 ACL用于QoS策略的流分类或用于报文过滤功能时：

· 对于VTEP设备发出的VXLAN报文和中间节点设备收到的VXLAN报文，IPv4 ACL仅支持匹配报文的外层IP头；

· 对于VTEP设备收到的VXLAN报文，IPv4 ACL仅支持匹配解封装后的VXLAN报文的内层IP头。

display acl all命令可以查看所有已存在的IPv4高级ACL规则、IPv4基本ACL规则。

删除规则时请注意：

· 使用undo rule rule-id命令时，必须指定一个已存在规则的编号。

· 使用undo rule rule-id命令时，如果没有指定任何可选参数，则删除整条规则；如果指定了可选参数，则只删除该参数所对应的内容。

· undo rule { deny | permit }命令无法删除规则中的部分内容。使用undo rule { deny | permit }命令时，必须输入已存在规则的完整形式。

counting参数用于开启本规则的匹配统计功能，而packet-filter命令中的hardware-count参数则用于开启指定ACL内所有规则的匹配统计功能。

【举例】

\# 为IPv4基本ACL 2000创建规则如下：仅允许来自10.0.0.0/8、172.17.0.0/16和192.168.1.0/24网段的报文通过，而拒绝来自所有其它网段的报文通过。

<Sysname> system-view

[Sysname] acl basic 2000

[Sysname-acl-ipv4-basic-2000] rule permit source 10.0.0.0 0.255.255.255

[Sysname-acl-ipv4-basic-2000] rule permit source 172.17.0.0 0.0.255.255

[Sysname-acl-ipv4-basic-2000] rule permit source 192.168.1.0 0.0.0.255

[Sysname-acl-ipv4-basic-2000] rule deny source any

【相关命令】

· acl

· acl logging interval

· display acl

· step

· time-range（ACL和QoS命令参考/时间段）


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-2032729963.htm -->

reset acl counter命令用来清除ACL的统计信息。

【命令】

reset acl [ ipv6 | mac | user-defined ] counter { acl-number | all | name acl-name }

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：清除指定编号ACL的统计信息。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

all：清除指定类型中全部ACL的统计信息。

name acl-name：清除指定名称ACL的统计信息。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

【使用指导】

如果未指定ipv6、mac或user-defined参数，则表示IPv4 ACL。

【举例】

\# 清除IPv4基本ACL 2001的统计信息。

<Sysname> reset acl counter 2001

【相关命令】

· display acl


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-2081707198.htm -->

display packet-filter命令用来显示ACL在报文过滤中的应用情况。

【命令】

display packet-filter { interface [ interface-type interface-number ] [ inbound | outbound ] | interface vlan-interface vlan-interface-number [ inbound | outbound ] [ slot slot-number ] }

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface [ interface-type interface-number ]：显示指定接口上ACL在报文过滤中的应用情况。interface-type interface-number表示接口类型和接口编号，这里的接口类型不包括VLAN接口。若未指定接口类型和接口编号，将显示除VLAN接口以外的所有接口上ACL在报文过滤中的应用情况。

interface vlan-interface vlan-interface-number：显示指定VLAN接口上ACL在报文过滤中的应用情况。vlan-interface-number表示VLAN接口的编号。

vlan [ vlan-id ]：显示指定VLAN中ACL在报文过滤中的应用情况。vlan-id表示VLAN的编号。若未指定VLAN编号，将显示所有VLAN中ACL在报文过滤中的应用情况。

inbound：显示入方向上ACL在报文过滤中的应用情况。

outbound：显示出方向上ACL在报文过滤中的应用情况。

slot slot-number：显示指定成员设备上ACL在报文过滤中的应用情况，slot-number表示设备在IRF中的成员编号。若未指定本参数，将显示主用设备上ACL在报文过滤中的应用情况。

【使用指导】

如果未指定inbound和outbound参数，将同时显示出、入方向上ACL在报文过滤中的应用情况。

【举例】

\# 显示接口Ten-GigabitEthernet1/0/1入方向上ACL在报文过滤中的应用情况。

<Sysname> display packet-filter interface ten-gigabitethernet 1/0/1 inbound

Interface: Ten-GigabitEthernet1/0/1

 Inbound policy:

 IPv4 ACL 2001

 IPv6 ACL 2002 (Failed)

 MAC ACL 4003, Hardware-count (Failed)

 IPv4 ACL 2004, Hardware-count (Failed)

 IPv4 default action: Deny

表1-2 display packet-filter命令显示信息描述表

| MAC default action | 报文过滤的缺省动作，包括： · Deny：报文过滤缺省动作为Deny应用成功 · Deny (Failed)：报文过滤缺省动作为Deny应用失败，实际动作仍为Permit · Permit：报文过滤缺省动作为Permit |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-324021376.htm -->

description命令用来配置ACL的描述信息。

undo description命令用来删除ACL的描述信息。

【命令】

description text

undo description

【缺省情况】

ACL没有任何描述信息。

【视图】

IPv4基本ACL视图/IPv4高级ACL视图

IPv6基本ACL视图/IPv6高级ACL视图

二层ACL视图

用户自定义ACL视图

【缺省用户角色】

network-admin

【参数】

text：表示ACL的描述信息，为1～127个字符的字符串，区分大小写。

【举例】

\# 为IPv4基本ACL 2000配置描述信息。

<Sysname> system-view

[Sysname] acl basic 2000

[Sysname-acl-ipv4-basic-2000] description This is an IPv4 basic ACL.

【相关命令】

· display acl


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-328695373.htm -->

rule命令用来为IPv6基本ACL创建一条规则。

undo rule命令用来为IPv6基本ACL删除一条规则或删除规则中的部分内容。

【命令】

rule [ rule-id ] { deny | permit } [ counting | fragment | logging | routing [ type routing-type ] | source { source-address source-prefix | source-address/source-prefix | any } | time-range time-range-name | vpn-instance vpn-instance-name ] *

undo rule rule-id [ counting | fragment | logging | routing | source | time-range | vpn-instance ] *

undo rule { deny | permit } [ counting | fragment | logging | routing [ type routing-type ] | source { source-address source-prefix | source-address/source-prefix | any } | time-range time-range-name | vpn-instance vpn-instance-name ] *

【缺省情况】

IPv6基本ACL内不存在任何规则。

【视图】

IPv6基本ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定IPv6基本ACL规则的编号，取值范围为0～65534。若未指定本参数，系统将从规则编号的起始值开始，自动分配一个大于现有最大编号的步长最小倍数。譬如现有规则的最大编号为28，步长为5，那么自动分配的新编号将是30。

deny：表示拒绝符合条件的报文。

permit：表示允许符合条件的报文。

counting：表示开启规则匹配统计功能，缺省为关闭。

fragment：表示仅对非首片分片报文有效，而对非分片报文和首片分片报文无效。若未指定本参数，表示该规则对非分片报文和分片报文均有效。

logging：表示对符合条件的报文可记录日志信息。该功能需要使用该ACL的模块支持日志记录功能，例如报文过滤。

routing [ type routing-type ]：表示对所有或指定类型的路由头有效，routing-type表示路由头类型的值，取值范围为0～255。若指定了type routing-type参数，表示仅对指定类型的路由头有效；否则，表示对IPv6所有类型的路由头都有效。

source { source-address source-prefix | source-address/source-prefix | any }：指定规则的源IPv6地址信息。source-address表示报文的源IPv6地址，source-prefix表示源IPv6地址的前缀长度，取值范围为1～128，any表示任意源IPv6地址。

time-range time-range-name：指定本规则生效的时间段。time-range-name表示时间段的名称，为1～32个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。若该时间段尚未配置，该规则仍会成功创建但系统将给出提示信息，并在该时间段的配置完成后此规则才会生效。有关时间段的详细介绍和具体配置过程，请参见“ACL和QoS配置指导”中的“时间段”。

vpn-instance vpn-instance-name：表示对指定VPN实例中的报文有效。vpn-instance-name表示MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写。若未指定本参数，表示该规则对非VPN报文和VPN报文均有效。

【使用指导】

使用rule命令时，如果指定编号的规则不存在，则创建一条新的规则；如果指定编号的规则已存在，则对旧规则进行修改，即在其原有内容的基础上叠加新的内容。

新创建或修改的规则不能与已有规则的内容完全相同，否则将提示出错，并导致该操作失败。

当ACL的规则匹配顺序为配置顺序时，允许修改该ACL内的任意一条已有规则；当ACL的规则匹配顺序为自动排序时，不允许修改该ACL内的已有规则，否则将提示出错。

display acl ipv6 all命令可以查看所有已存在的IPv6高级ACL规则与IPv6基本ACL规则。

删除规则时请注意：

· 使用undo rule rule-id命令时，必须指定一个已存在规则的编号。

· 使用undo rule rule-id命令时，如果没有指定任何可选参数，则删除整条规则；如果指定了可选参数，则只删除该参数所对应的内容。

· undo rule { deny | permit }命令无法删除规则中的部分内容。使用undo rule { deny | permit }命令时，必须输入已存在规则的完整形式。

counting参数用于开启本规则的匹配统计功能，而packet-filter ipv6命令中的hardware-count参数则用于开启指定ACL内所有规则的匹配统计功能。

【举例】

\# 为IPv6基本ACL 2000创建规则如下：仅允许来自1001::/16、3124:1123::/32和FE80:5060:1001::/48网段的报文通过，而拒绝来自所有其它网段的报文通过。

<Sysname> system-view

[Sysname] acl ipv6 basic 2000

[Sysname-acl-ipv6-basic-2000] rule permit source 1001:: 16

[Sysname-acl-ipv6-basic-2000] rule permit source 3124:1123:: 32

[Sysname-acl-ipv6-basic-2000] rule permit source fe80:5060:1001:: 48

[Sysname-acl-ipv6-basic-2000] rule deny source any

【相关命令】

· acl

· acl logging interval

· display acl

· step

· time-range（ACL和QoS命令参考/时间段）


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-57944529.htm -->

acl trap interval命令用来配置报文过滤告警信息的生成与发送周期。

undo acl trap interval命令用来恢复缺省情况。

【命令】

acl trap interval interval

undo acl trap interval

【缺省情况】

报文过滤日告警信息的生成与发送周期为0分钟，即不记录报文过滤的告警信息。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

interval：报文过滤告警信息的生成与发送周期，取值范围为0～1440，且必须为5的整数倍，0表示不进行记录，单位为分钟。

【使用指导】

系统只支持对应用IPv4基本ACL、IPv4高级ACL、IPv6基本ACL或IPv6高级ACL进行报文过滤的报文过滤告警信息进行记录，且在上述ACL中配置规则时必须指定logging参数。

设备周期性地生成告警信息并发送到SNMP模块，包括该周期内被匹配的报文数量以及所使用的ACL规则。同时，还会对匹配规则的数据流的第一个数据包进行记录并送到SNMP模块。有关告警信息的详细介绍，请参见“网络管理和监控配置指导”中的“SNMP”。

【举例】

\# 配置IPv4报文过滤告警信息的生成与发送周期为10分钟。

<Sysname> system-view

[Sysname] acl trap interval 10

【相关命令】

· rule (IPv4 advanced ACL view)

· rule (IPv4 basic ACL view)

· rule (IPv6 advanced ACL view)

· rule (IPv6 basic ACL view)


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-62066971.htm -->

display acl命令用来显示ACL的配置和运行情况。

【命令】

display acl [ ipv6 | mac | user-defined ] { acl-number | all | name acl-name }

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：显示指定编号的ACL的配置和运行情况。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

all：显示指定类型中全部ACL的配置和运行情况。

name acl-name：显示指定名称的ACL的配置和运行情况。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

【使用指导】

本命令将按照实际匹配顺序来排列ACL内的规则，即：当ACL的规则匹配顺序为配置顺序时，各规则将按照编号由小到大排列；当ACL的规则匹配顺序为自动排序时，各规则将按照“深度优先”原则由深到浅排列。

如果未指定ipv6、mac、user-defined参数，则表示IPv4 ACL。

【举例】

\# 显示IPv4基本ACL 2001的配置和运行情况。

<Sysname> display acl 2001

Basic IPv4 ACL 2001, 1 rules, match-order is auto,

This is an IPv4 basic ACL.

ACL's step is 5, start ID is 0

 rule 5 permit source 1.1.1.1 0

 rule 5 comment This rule is used on Ten-GigabitEthernet1/0/1.

表1-1 display acl命令显示信息描述表

| rule 5 comment This rule is used on Ten-GigabitEthernet1/0/1. | 规则5的描述信息 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-667277990.htm -->

rule命令用来为用户自定义ACL创建一条规则。

undo rule命令用来为用户自定义ACL删除一条规则。

【命令】

rule [ rule-id ] { deny | permit } [ { l2 rule-string rule-mask offset }&<1-8> ] [ counting | time-range time-range-name ] *

undo rule rule-id

undo rule { deny | permit } [ { l2 rule-string rule-mask offset }&<1-8> ] [ counting | time-range time-range-name ] *

【缺省情况】

用户自定义ACL内不存在任何规则。

【视图】

用户自定义ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定用户自定义ACL规则的编号，取值范围为0～65534。若未指定本参数，系统将按照步长为5从0开始，自动分配一个大于现有最大编号的步长最小倍数。譬如现有规则的最大编号为28，步长为5，那么自动分配的新编号将是30。

deny：表示拒绝符合条件的报文。

permit：表示允许符合条件的报文。

l2：表示从L2帧头开始偏移。

rule-string：指定用户自定义的规则字符串，必须是16进制数组成，字符长度必须是偶数。

rule-mask：指定规则字符串的掩码，用于和报文作“与”操作，必须是16进制数组成，字符长度必须是偶数，且必须与rule-string的长度相同。

offset：指定偏移量，它以用户指定的报文头部为基准，指定从第几个字节开始进行比较。

&<1-8>：表示前面的参数最多可以输入8次。

counting：表示开启规则匹配统计功能，缺省为关闭。

time-range time-range-name：指定本规则生效的时间段。time-range-name表示时间段的名称，为1～32个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。若该时间段尚未配置，该规则仍会成功创建但系统将给出提示信息，并在该时间段的配置完成后此规则才会生效。有关时间段的详细介绍和具体配置过程，请参见“ACL和QoS配置指导”中的“时间段”。

【使用指导】

使用rule命令时，如果指定编号的规则不存在，则创建一条新的规则；如果指定编号的规则已存在，则对旧规则进行修改，即在其原有内容的基础上叠加新的内容。

新创建的规则不能与已有规则的内容完全相同，否则将提示出错，并导致创建失败。

display acl user-defined all命令可以查看所有已存在的用户自定义ACL规则。

删除规则时请注意：

· 使用undo rule rule-id命令时，必须指定一个已存在规则的编号。

· 使用undo rule { deny | permit }命令时，必须输入已存在规则的完整形式。

· undo rule rule-id命令与undo rule { deny | permit }均无法删除规则中的部分内容。

counting参数用于开启本规则的匹配统计功能，而packet-filter命令中的hardware-count参数则用于开启指定ACL内所有规则的匹配统计功能。

【举例】

\# 为用户自定义ACL 5005创建规则如下：允许从L2帧头开始算起第13、14两字节的内容为0x0806的报文（即ARP报文）通过。

<Sysname> system-view

[Sysname] acl user-defined 5005

[Sysname-acl-user-5005] rule permit l2 0806 ffff 12

【相关命令】

· acl

· display acl

· time-range（ACL和QoS命令参考/时间段）


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_-799344228.htm -->

rule命令用来为IPv4高级ACL创建一条规则。

undo rule命令用来为IPv4高级ACL删除一条规则或删除规则中的部分内容。

【命令】

rule [ rule-id ] { deny | permit } protocol [ { { ack ack-value | fin fin-value | psh psh-value | rst rst-value | syn syn-value | urg urg-value } * | established } | counting | destination { dest-address dest-wildcard | any } | destination-port operator port1 [ port2 ] | { dscp dscp | { precedence precedence | tos tos } * } | fragment | icmp-type { icmp-type [ icmp-code ] | icmp-message } | logging | source { source-address source-wildcard | any } | source-port operator port1 [ port2 ] | time-range time-range-name | vpn-instance vpn-instance-name ] *

undo rule rule-id [ { { ack | fin | psh | rst | syn | urg } * | established } | counting | destination | destination-port | { dscp | { precedence | tos } * } | fragment | icmp-type | logging | source | source-port | time-range | vpn-instance ] *

undo rule { deny | permit } protocol [ { { ack ack-value | fin fin-value | psh psh-value | rst rst-value | syn syn-value | urg urg-value } * | established } | counting | destination { dest-address dest-wildcard | any } | destination-port operator port1 [ port2 ] | { dscp dscp | { precedence precedence | tos tos } * } | fragment | icmp-type { icmp-type [ icmp-code ] | icmp-message } | logging | source { source-address source-wildcard | any } | source-port operator port1 [ port2 ] | time-range time-range-name | vpn-instance vpn-instance-name ] *

【缺省情况】

IPv4高级ACL内不存在任何规则。

【视图】

IPv4高级ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定IPv4高级ACL规则的编号，取值范围为0～65534。若未指定本参数，系统将从规则编号的起始值开始，自动分配一个大于现有最大编号的步长最小倍数。譬如现有规则的最大编号为28，步长为5，那么自动分配的新编号将是30。

deny：表示拒绝符合条件的报文。

permit：表示允许符合条件的报文。

protocol：表示IPv4承载的协议类型，可输入的形式如下：

· 数字：取值范围为0～255；

· 名称（括号内为对应的数字）：可选取gre（47）、icmp（1）、igmp（2）、ip、ipinip（4）、ospf（89）、tcp（6）或udp（17）。ip表示所有协议类型。

protocol之后可配置如[表1-7](#_Ref295383134)所示的规则信息参数。

表1-7 规则信息参数

| vpn-instance vpn-instance-name | VPN实例 | 对指定VPN实例中的报文有效 | vpn-instance-name：MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写 若未指定本参数，表示该规则对非VPN报文和VPN报文均有效 |
| --- | --- | --- | --- |

当protocol为tcp（6）或udp（17）时，用户还可配置如[表1-8](#_Ref259115846)所示的规则信息参数。

表1-8 TCP/UDP特有的规则信息参数

| established | TCP连接建立标识 | 定义对TCP连接报文的处理规则 | TCP协议特有的参数 用于定义TCP报文中ACK或RST标志位为1的报文 |
| --- | --- | --- | --- |

当protocol为icmp（1）时，用户还可配置如[表1-9](#_Ref295383166)所示的规则信息参数。

表1-9 ICMP特有的规则信息参数

| icmp-type { icmp-type icmp-code \| icmp-message } | ICMP报文的消息类型和消息码信息 | 指定本规则中ICMP报文的消息类型和消息码信息 | icmp-type：ICMP消息类型，取值范围为0～255 icmp-code：ICMP消息码，取值范围为0～255 icmp-message：ICMP消息名称。可以输入的ICMP消息名称，及其与消息类型和消息码的对应关系如[表1-10](#_Ref144979012)所示 |
| --- | --- | --- | --- |

表1-10 ICMP消息名称与消息类型和消息码的对应关系

| ttl-exceeded | 11 | 0 |
| --- | --- | --- |

【使用指导】

使用rule命令时，如果指定编号的规则不存在，则创建一条新的规则；如果指定编号的规则已存在，则对旧规则进行修改，即在其原有内容的基础上叠加新的内容。

新创建或修改的规则不能与已有规则的内容完全相同，否则将提示出错，并导致该操作失败。

当ACL的规则匹配顺序为配置顺序时，允许修改该ACL内的任意一条已有规则；当ACL的规则匹配顺序为自动排序时，不允许修改该ACL内的已有规则，否则将提示出错。

在VXLAN组网中，当IPv4 ACL用于QoS策略的流分类或用于报文过滤功能时：

· 对于VTEP设备发出的VXLAN报文和中间节点设备收到的VXLAN报文，IPv4 ACL仅支持匹配报文的外层IP头；

· 对于VTEP设备收到的VXLAN报文，IPv4 ACL仅支持匹配解封装后的VXLAN报文的内层IP头。

display acl all命令可以查看所有已存在的IPv4高级ACL规则、IPv4基本ACL规则。

删除规则时请注意：

· 使用undo rule rule-id命令时，必须指定一个已存在规则的编号。

· 使用undo rule rule-id命令时，如果没有指定任何可选参数，则删除整条规则；如果指定了可选参数，则只删除该参数所对应的内容。

· undo rule { deny | permit }命令无法删除规则中的部分内容。使用undo rule { deny | permit }命令时，必须输入已存在规则的完整形式。

【举例】

\# 为IPv4高级ACL 3000创建规则如下：允许129.9.0.0/16网段内的主机与202.38.160.0/24网段内主机的WWW端口（端口号为80）建立连接。

<Sysname> system-view

[Sysname] acl advanced 3000

[Sysname-acl-ipv4-adv-3000] rule permit tcp source 129.9.0.0 0.0.255.255 destination 202.38.160.0 0.0.0.255 destination-port eq 80

\# 为IPv4高级ACL 3001创建规则如下：允许IP报文通过，但拒绝发往192.168.1.0/24网段的ICMP报文通过。

<Sysname> system-view

[Sysname] acl advanced 3001

[Sysname-acl-ipv4-adv-3001] rule deny icmp destination 192.168.1.0 0.0.0.255

[Sysname-acl-ipv4-adv-3001] rule permit ip

\# 为IPv4高级ACL 3002创建规则如下：在出、入双方向上都允许建立FTP连接并传输FTP数据。

<Sysname> system-view

[Sysname] acl advanced 3002

[Sysname-acl-ipv4-adv-3002] rule permit tcp source-port eq ftp

[Sysname-acl-ipv4-adv-3002] rule permit tcp source-port eq ftp-data

[Sysname-acl-ipv4-adv-3002] rule permit tcp destination-port eq ftp

[Sysname-acl-ipv4-adv-3002] rule permit tcp destination-port eq ftp-data

\# 为IPv4高级ACL 3003创建规则如下：在出、入双方向上都允许SNMP报文和SNMP Trap报文通过。

<Sysname> system-view

[Sysname] acl advanced 3003

[Sysname-acl-ipv4-adv-3003] rule permit udp source-port eq snmp

[Sysname-acl-ipv4-adv-3003] rule permit udp source-port eq snmptrap

[Sysname-acl-ipv4-adv-3003] rule permit udp destination-port eq snmp

[Sysname-acl-ipv4-adv-3003] rule permit udp destination-port eq snmptrap

【相关命令】

· acl

· acl logging interval

· display acl

· step

· time-range（ACL和QoS命令参考/时间段）


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1007168409.htm -->

packet-filter default deny命令用来配置报文过滤的缺省动作为Deny，即禁止未匹配上ACL规则的报文通过。

undo packet-filter default deny命令用来恢复缺省情况。

【命令】

packet-filter default deny

undo packet-filter default deny

【缺省情况】

报文过滤的缺省动作为Permit，即允许未匹配上ACL规则的报文通过。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

配置报文过滤的缺省动作会在所有的应用对象下添加一个缺省动作应用，该应用也会像其它应用的ACL一样显示。

【举例】

\# 配置报文过滤的缺省动作为Deny。

<Sysname> system-view

[Sysname] packet-filter default deny

【相关命令】

· display packet-filter

· display packet-filter statistics

· display packet-filter verbose


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1193000589.htm -->

rule命令用来为IPv6高级ACL创建一条规则。

undo rule命令用来为IPv6高级ACL删除一条规则或删除规则中的部分内容。

【命令】

rule [ rule-id ] { deny | permit } protocol [ { { ack ack-value | fin fin-value | psh psh-value | rst rst-value | syn syn-value | urg urg-value } * | established } | counting | destination { dest-address dest-prefix | dest-address/dest-prefix | any } | destination-port operator port1 [ port2 ] | dscp dscp | flow-label flow-label-value | fragment | icmp6-type { icmp6-type icmp6-code | icmp6-message } | logging | routing [ type routing-type ] | hop-by-hop [ type hop-type ] | source { source-address source-prefix | source-address/source-prefix | any } | source-port operator port1 [ port2 ] | time-range time-range-name | vpn-instance vpn-instance-name ] *

undo rule rule-id [ { { ack | fin | psh | rst | syn | urg } * | established } | counting | destination | destination-port | dscp | flow-label | fragment | icmp6-type | logging | routing | hop-by-hop | source | source-port | time-range | vpn-instance ] *

undo rule { deny | permit } protocol [ { { ack ack-value | fin fin-value | psh psh-value | rst rst-value | syn syn-value | urg urg-value } * | established } | counting | destination { dest-address dest-prefix | dest-address/dest-prefix | any } | destination-port operator port1 [ port2 ] | dscp dscp | flow-label flow-label-value | fragment | icmp6-type { icmp6-type icmp6-code | icmp6-message } | logging | routing [ type routing-type ] | hop-by-hop [ type hop-type ] | source { source-address source-prefix | source-address/source-prefix | any } | source-port operator port1 [ port2 ] | time-range time-range-name | vpn-instance vpn-instance-name ] *

【缺省情况】

IPv6高级ACL内不存在任何规则。

【视图】

IPv6高级ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定IPv6高级ACL规则的编号，取值范围为0～65534。若未指定本参数，系统将从规则编号的起始值开始，自动分配一个大于现有最大编号的步长最小倍数。譬如现有规则的最大编号为28，步长为5，那么自动分配的新编号将是30。

deny：表示拒绝符合条件的报文。

permit：表示允许符合条件的报文。

protocol：表示IPv6承载的协议类型，可输入的形式如下：

· 数字：取值范围为0～255；

· 名称（括号内为对应的数字）：可选取gre（47）、icmpv6（58）、ipv6、ipv6-ah（51）、ipv6-esp（50）、ospf（89）、tcp（6）或udp（17）。ipv6表示所有协议类型。

protocol之后可配置如[表1-11](#_Ref259116285)所示的规则信息参数。

表1-11 规则信息参数

| vpn-instance vpn-instance-name | VPN实例 | 对指定VPN实例中的报文有效 | vpn-instance-name：MPLS L3VPN的VPN实例名称，为1～31个字符的字符串，区分大小写 若未指定本参数，表示该规则对非VPN报文和VPN报文均有效 |
| --- | --- | --- | --- |

当protocol为tcp（6）或udp（17）时，用户还可配置如[表1-12](#_Ref259116335)所示的规则信息参数。

表1-12 TCP/UDP特有的规则信息参数

| established | TCP连接建立标识 | 定义对TCP连接报文的处理规则 | TCP协议特有的参数 用于定义TCP报文中ACK或RST标志位为1的报文 |
| --- | --- | --- | --- |

当protocol为icmpv6（58）时，用户还可配置如[表1-13](#_Ref259116368)所示的规则信息参数。

表1-13 ICMPv6特有的规则信息参数

| icmp6-type { icmp6-type icmp6-code \| icmp6-message } | ICMPv6报文的消息类型和消息码 | 指定本规则中ICMPv6报文的消息类型和消息码信息 | icmp6-type：ICMPv6消息类型，取值范围为0～255 icmp6-code：ICMPv6消息码，取值范围为0～255 icmp6-message：ICMPv6消息名称。可以输入的ICMPv6消息名称，及其与消息类型和消息码的对应关系如[表1-14](#_Ref139034904)所示 |
| --- | --- | --- | --- |

表1-14 ICMPv6消息名称与消息类型和消息码的对应关系

| unknown-next-hdr | 4 | 1 |
| --- | --- | --- |

【使用指导】

当ACL用于QoS策略的流分类或报文过滤功能时，如果QoS策略或报文过滤功能应用于出方向，则不支持配置flow-label参数。

当ACL用于报文过滤功能时，不支持配置fragment参数。

使用rule命令时，如果指定编号的规则不存在，则创建一条新的规则；如果指定编号的规则已存在，则对旧规则进行修改，即在其原有内容的基础上叠加新的内容。

新创建或修改的规则不能与已有规则的内容完全相同，否则将提示出错，并导致该操作失败。

当ACL的规则匹配顺序为配置顺序时，允许修改该ACL内的任意一条已有规则；当ACL的规则匹配顺序为自动排序时，不允许修改该ACL内的已有规则，否则将提示出错。

display acl ipv6 all命令可以查看所有已存在的IPv6高级ACL规则与IPv6基本ACL规则。

删除规则时请注意：

· 使用undo rule rule-id命令时，必须指定一个已存在规则的编号。

· 使用undo rule rule-id命令时，如果没有指定任何可选参数，则删除整条规则；如果指定了可选参数，则只删除该参数所对应的内容。

· undo rule { deny | permit }命令无法删除规则中的部分内容。使用undo rule { deny | permit }命令时，必须输入已存在规则的完整形式。

【举例】

\# 为IPv6高级ACL 3000创建规则如下：允许2030:5060::/64网段内的主机与FE80:5060::/96网段内主机的WWW端口（端口号为80）建立连接。

<Sysname> system-view

[Sysname] acl ipv6 advanced 3000

[Sysname-acl-ipv6-adv-3000] rule permit tcp source 2030:5060::/64 destination fe80:5060::/96 destination-port eq 80

\# 为IPv6高级ACL 3001创建规则如下：允许IPv6报文通过，但拒绝发往FE80:5060:1001::/48网段的ICMPv6报文通过。

<Sysname> system-view

[Sysname] acl ipv6 advanced 3001

[Sysname-acl-ipv6-adv-3001] rule deny icmpv6 destination fe80:5060:1001:: 48

[Sysname-acl-ipv6-adv-3001] rule permit ipv6

\# 为IPv6高级ACL 3002创建规则如下：在出、入双方向上都允许建立FTP连接并传输FTP数据。

<Sysname> system-view

[Sysname] acl ipv6 advanced 3002

[Sysname-acl-ipv6-adv-3002] rule permit tcp source-port eq ftp

[Sysname-acl-ipv6-adv-3002] rule permit tcp source-port eq ftp-data

[Sysname-acl-ipv6-adv-3002] rule permit tcp destination-port eq ftp

[Sysname-acl-ipv6-adv-3002] rule permit tcp destination-port eq ftp-data

\# 为IPv6高级ACL 3003创建规则如下：在出、入双方向上都允许SNMP报文和SNMP Trap报文通过。

<Sysname> system-view

[Sysname] acl ipv6 advanced 3003

[Sysname-acl-ipv6-adv-3003] rule permit udp source-port eq snmp

[Sysname-acl-ipv6-adv-3003] rule permit udp source-port eq snmptrap

[Sysname-acl-ipv6-adv-3003] rule permit udp destination-port eq snmp

[Sysname-acl-ipv6-adv-3003] rule permit udp destination-port eq snmptrap

\# 为IPv6高级ACL 3004创建规则如下：在含有逐跳头的报文中，只允许转发含有MLD选项（Type＝5）的报文，丢弃其他报文。

<Sysname> system-view

[Sysname] acl ipv6 advanced 3004

[Sysname-acl-ipv6-adv-3004] rule permit ipv6 hop-by-hop type 5

[Sysname-acl-ipv6-adv-3004] rule deny ipv6 hop-by-hop

【相关命令】

· acl

· acl logging interval

· display acl

· step

· time-range（ACL和QoS命令参考/时间段）


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_12865098.htm -->

display packet-filter statistics sum命令用来显示ACL在报文过滤中应用的累加统计信息。

【命令】

display packet-filter statistics sum { inbound | outbound } [ ipv6 | mac | user-defined ] { acl-number | name acl-name } [ brief ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

inbound：显示入方向上ACL在报文过滤中应用的累加统计信息。

outbound：显示出方向上ACL在报文过滤中应用的累加统计信息。

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：显示指定编号ACL在报文过滤中应用的累加统计信息。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name acl-name：显示指定名称ACL在报文过滤中应用的累加统计信息。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

brief：显示ACL在报文过滤中应用的简要累加统计信息。

【使用指导】

如果未指定ipv6、mac或user-defined参数，则表示IPv4 ACL。

【举例】

\# 显示入方向上IPv4基本ACL 2001在报文过滤中应用的累加统计信息。

<Sysname> display packet-filter statistics sum inbound 2001

Sum:

 Inbound policy:

 IPv4 ACL 2001

 rule 0 permit source 2.2.2.2 0 (2 packets)

 rule 5 permit source 1.1.1.1 0

 rule 10 permit vpn-instance test

 Totally 2 packets permitted, 0 packets denied

 Totally 100% permitted, 0% denied

\# 显示入方向上IPv4基本ACL 2000在报文过滤中应用的简要累加统计信息。

<Sysname> display packet-filter statistics sum inbound 2000 brief

Sum:

 Inbound policy:

 IPv4 ACL 2000

 Totally 2 packets permitted, 0 packets denied

 Totally 100% permitted, 0% denied

表1-4 display packet-filter statistics sum命令显示信息描述表

| Totally 100% permitted, 0% denied | 该ACL允许符合条件报文的通过率和拒绝符合条件报文的丢弃率 |
| --- | --- |

【相关命令】

· reset packet-filter statistics


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1424558911.htm -->

display packet-filter statistics命令用来显示ACL在报文过滤中应用的统计信息。

【命令】

display packet-filter statistics interface interface-type interface-number { inbound | outbound } [ [ ipv6 | mac | user-defined ] { acl-number | name acl-name } ] [ brief ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface interface-type interface-number：显示指定接口上的统计信息。interface-type interface-number表示接口类型和接口编号。

inbound：显示入方向上的统计信息。

outbound：显示出方向上的统计信息。

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：显示指定编号ACL在报文过滤中应用的统计信息。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name acl-name：显示指定名称ACL在报文过滤中应用的统计信息。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

brief：显示简要统计信息。

【使用指导】

如果未指定acl-number、name acl-name和ACL类型（ipv6、mac、user-defined）参数，将显示全部ACL在报文过滤中应用的统计信息。

如果未指定ipv6、mac或user-defined参数，则表示IPv4 ACL。

【举例】

\# 显示接口Ten-GigabitEthernet1/0/1入方向上全部ACL在报文过滤中应用的统计信息。

<Sysname> display packet-filter statistics interface ten-gigabitethernet 1/0/1 inbound

Interface: Ten-GigabitEthernet1/0/1

 Inbound policy:

 IPv4 ACL 2001, Hardware-count

 From 2011-06-04 10:25:21 to 2011-06-04 10:35:57

 rule 0 permit source 2.2.2.2 0 (2 packets)

 rule 5 permit source 1.1.1.1 0 (Failed)

 rule 10 permit vpn-instance test (No resource)

 Totally 2 packets permitted, 0 packets denied

 Totally 100% permitted, 0% denied

 IPv4 ACL 2002 (Failed)

 MAC ACL 4000

 From 2011-06-04 10:25:34 to 2011-06-04 10:35:57

 rule 0 permit

 IPv6 ACL 2000

 IPv4 default action: Deny

 MAC default action: Deny

表1-3 display packet-filter statistics命令显示信息描述表

| Totally 7 packets | 报文过滤缺省动作的执行次数 |
| --- | --- |

【相关命令】

· reset packet-filter statistics


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1501971835.htm -->

reset packet-filter statistics命令用来清除ACL在报文过滤中应用的统计信息、累加统计信息。

【命令】

reset packet-filter statistics interface [ interface-type interface-number ] { inbound | outbound } [ [ ipv6 | mac | user-defined ] { acl-number | name acl-name } ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

interface [ interface-type interface-number ]：清除指定接口上的统计信息。interface-type interface-number表示接口类型和接口编号。若未指定接口类型和接口编号，将清除所有接口上的统计信息。

inbound：清除入方向上的统计信息。

outbound：清除出方向上的统计信息。

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：清除指定编号ACL在报文过滤中应用的统计信息。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name acl-name：清除指定名称ACL在报文过滤中应用的统计信息。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

【使用指导】

如果未指定acl-number、name acl-name和ACL类型（ipv6、mac、user-defined）参数，将清除全部ACL在报文过滤中应用的统计信息。

如果未指定ipv6、mac或user-defined参数，则表示IPv4 ACL。

【举例】

\# 清除在接口Ten-GigabitEthernet1/0/1入方向上IPv4基本ACL 2001在报文过滤中应用的统计信息。

<Sysname> reset packet-filter statistics interface ten-gigabitethernet 1/0/1 inbound 2001

【相关命令】

· display packet-filter statistics

· display packet-filter statistics sum


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1593067156.htm -->

packet-filter filter命令用来配置报文过滤在VLAN接口的生效范围。

undo packet-filter filter命令用来恢复默认情况。

【命令】

packet-filter filter { route | all }

undo packet-filter filter

【缺省情况】

报文过滤仅对通过VLAN接口进行三层转发的报文生效。

【视图】

VLAN接口视图

【缺省用户角色】

network-admin

【参数】

route：表示报文过滤仅对通过VLAN接口进行三层转发的报文生效。

all：表示报文过滤对所有报文（包括通过VLAN接口进行三层转发的报文和通过VLAN接口对应的物理接口进行二层转发的报文）均生效。

【举例】

\# 配置VLAN接口2上的报文过滤方式为route，即报文过滤仅对通过VLAN接口2进行三层转发的报文生效。

<Sysname> system-view

[Sysname] interface vlan-interface 2

[Sysname-Vlan-interface2] packet-filter filter route


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1792029913.htm -->

display qos-acl resource命令用来显示QoS和ACL资源的使用情况。

【命令】

display qos-acl resource [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

slot slot-number：显示指定成员设备上QoS和ACL资源的使用情况，slot-number表示设备在IRF中的成员编号。若未指定本参数，将显示IRF中所有成员设备上QoS和ACL资源的使用情况。

【举例】

\# 显示QoS和ACL资源的使用情况。

<Sysname> display qos-acl resource

Interfaces: FGE9/0/1 to FGE9/0/19, XGE9/0/20:1 to XGE9/0/20:4

 XGE9/0/21:1 to XGE9/0/21:4, XGE9/0/22:1 to XGE9/0/22:4

 XGE9/0/23:1 to XGE9/0/23:4, XGE9/0/24:1 to XGE9/0/24:4

 XGE9/0/25:1 to XGE9/0/25:4, XGE9/0/26:1 to XGE9/0/26:4

 XGE9/0/27:1 to XGE9/0/27:4, XGE9/0/28:1 to XGE9/0/28:4

 FGE9/0/29 to FGE9/0/32 (slot 9)

---------------------------------------------------------------------

 Type Total Reserved Configured Remaining Usage

---------------------------------------------------------------------

 VFP ACL 1024 261 0 763 25%

 IFP ACL 16384 14336 8 2040 87%

 IFP Meter 8192 7168 0 1024 87%

 IFP Counter 8192 7168 2 1022 87%

 EFP ACL 1024 0 3 1021 0%

 EFP Meter 512 0 0 512 0%

 EFP Counter 512 0 0 512 0%

表1-6 display qos-acl resource命令显示信息描述表

| Usage | 预留的资源数与已配置的资源数之和占资源总数的百分比，分子按实际计算结果的整数部分显示，例如实际计算结果为50.8%，此处显示为50%。 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_1954696934.htm -->

acl命令用来创建ACL，并进入ACL视图。如果指定的ACL已存在，则直接进入ACL视图。

undo acl命令用来删除指定或全部ACL。

【命令】

acl [ ipv6 ] { advanced | basic } { acl-number | name acl-name } [ match-order { auto | config } ]

acl mac { acl-number | name acl-name } [ match-order { auto | config } ]

acl user-defined { acl-number | name acl-name }

undo acl [ ipv6 ] { all | { advanced | basic } { acl-number | name acl-name } }

undo acl mac { all | acl-number | name acl-name }

undo acl user-defined { all | acl-number | name acl-name }

【缺省情况】

不存在ACL。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

ipv6：指定ACL类型为IPv6 ACL。如果未指定本参数，则表示IPv4 ACL。

basic：指定创建基本ACL。

advanced：指定创建高级ACL。

mac：指定创建二层ACL。

user-defined：指定创建用户自定义ACL。

acl-number：指定ACL的编号。acl-number表示ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name acl-name：指定ACL的名称。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。为避免混淆，ACL的名称不允许使用英文单词all。

match-order { auto | config }：指定规则的匹配顺序，auto表示按照自动排序（即“深度优先”原则）的顺序进行规则匹配，config表示按照配置顺序进行规则匹配。缺省情况下，规则的匹配顺序为配置顺序。用户自定义ACL不支持本参数，其规则匹配顺序只能为配置顺序。

all：指定类型中全部ACL。

【使用指导】

当ACL内不存在任何规则时，用户可以使用本命令对该ACL的规则匹配顺序进行修改，否则不允许进行修改。

如果ACL规则的匹配项中包含了除IP五元组（源IP地址、源端口号、目的IP地址、目的端口号、传输层协议）、ICMP报文或ICMPv6报文的消息类型和消息码信息、VPN实例、日志操作和时间段之外的其它匹配项，则设备转发ACL匹配的这类报文时会启用慢转发流程。慢转发时设备会将报文上送控制平面，计算报文相应的表项信息。执行慢转发流程时，设备的转发能力将会有所降低。

【举例】

\# 创建一个编号为2000的IPv4基本ACL，并进入其视图。

<Sysname> system-view

[Sysname] acl basic 2000

[Sysname-acl-ipv4-basic-2000]

\# 创建一个IPv4基本ACL，指定其名称为flow，并进入其视图。

<Sysname> system-view

[Sysname] acl basic name flow

[Sysname-acl-ipv4-basic-flow]

\# 创建一个编号为3000的IPv4高级ACL，并进入其视图。

<Sysname> system-view

[Sysname] acl advanced 3000

[Sysname-acl-ipv4-adv-3000]

\# 创建一个编号为2000的IPv6基本ACL，并进入其视图。

<Sysname> system-view

[Sysname] acl ipv6 basic 2000

[Sysname-acl-ipv6-basic-2000]

\# 创建一个IPv6基本ACL，其名称为flow，并进入其视图。

<Sysname> system-view

[Sysname] acl ipv6 basic name flow

[Sysname-acl-ipv6-basic-flow]

\# 创建一个IPv6高级ACL，其名称为abc，并进入其视图。

<Sysname> system-view

[Sysname] acl ipv6 advanced name abc

[Sysname-acl-ipv6-adv-abc]

\# 创建一个编号为4000的二层ACL，并进入其视图。

<Sysname> system-view

[Sysname] acl mac 4000

[Sysname-acl-mac-4000]

\# 创建一个二层ACL，其名称为flow，并进入其视图。

<Sysname> system-view

[Sysname] acl mac name flow

[Sysname-acl-mac-flow]

\# 创建一个编号为5000的用户自定义ACL，并进入其视图。

<Sysname> system-view

[Sysname] acl user-defined 5000

[Sysname-acl-user-5000]

\# 创建一个用户自定义ACL，其名称为flow，并进入其视图。

<Sysname> system-view

[Sysname] acl user-defined name flow

[Sysname-acl-user-flow]

【相关命令】

· display acl


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_2082066590.htm -->

acl copy命令用来复制并生成一个新的ACL。

【命令】

acl [ ipv6 | mac | user-defined ] copy { source-acl-number | name source-acl-name } to { dest-acl-number | name dest-acl-name }

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

source-acl-number：指定源ACL的编号，该ACL必须存在。本参数的取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name source-acl-name：指定源ACL的名称，该ACL必须存在。source-acl-name为1～63个字符的字符串，不区分大小写。

dest-acl-number：指定目的ACL的编号，该ACL必须不存在。本参数的取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name dest-acl-name：指定目的ACL的名称，该ACL必须不存在。dest-acl-name为1～63个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。为避免混淆，ACL的名称不允许使用英文单词all。

【使用指导】

目的ACL的类型要与源ACL的类型相同。

除了ACL的编号或名称不同外，新生成的ACL（即目的ACL）的匹配顺序、规则匹配统计功能的开启情况、规则编号的步长、所包含的规则、规则的描述信息以及ACL的描述信息等都与源ACL的相同。

若未指定ipv6、mac或user-defined参数，则表示IPv4 ACL。

【举例】

\# 通过复制已存在的IPv4基本ACL 2001，来生成一个新的编号为2002的同类型ACL。

<Sysname> system-view

[Sysname] acl copy 2001 to 2002

\# 通过复制已存在的IPv4基本ACL test，来生成名为paste的同类型ACL。

<Sysname> system-view

[Sysname] acl copy name test to name paste


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_2090008576.htm -->

packet-filter命令用来在接口上应用ACL进行报文过滤。

undo packet-filter命令用来取消在接口上应用ACL进行报文过滤。

【命令】

packet-filter [ ipv6 | mac | user-defined ] { acl-number | name acl-name } { inbound | outbound } [ hardware-count ]

undo packet-filter [ ipv6 | mac | user-defined ] { acl-number | name acl-name } { inbound | outbound }

【缺省情况】

接口不对报文进行过滤。

【视图】

二层以太网接口视图/二层聚合接口视图/三层以太网接口视图/三层聚合接口视图/VLAN接口视图/VSI虚接口

【缺省用户角色】

network-admin

【参数】

ipv6：指定ACL类型为IPv6 ACL。

mac：指定ACL类型为二层ACL。

user-defined：指定ACL类型为用户自定义ACL。

acl-number：指定ACL的编号，取值范围及其代表的ACL类型如下：

· 2000～2999：表示基本ACL。

· 3000～3999：表示高级ACL。

· 4000～4999：表示二层ACL。

· 5000～5999：表示用户自定义ACL。

name acl-name：指定ACL的名称。acl-name表示ACL的名称，为1～63个字符的字符串，不区分大小写。

inbound：对收到的报文进行过滤。

outbound：对发出的报文进行过滤。

hardware-count：表示开启规则匹配统计功能，缺省为关闭。

【使用指导】

若未指定ipv6、mac或user-defined关键字，则表示IPv4 ACL。

本命令中的hardware-count参数用于开启指定ACL内所有规则的匹配统计功能，而rule命令中的counting参数则用于开启当前规则的匹配统计功能。

如果设备资源不足，必须先执行undo packet-filter命令取消报文过滤，然后再配置不携带hardware-count关键字的报文过滤，以此关闭规则匹配统计功能。

如果设备资源充足，可通过不携带hardware-count关键字重新配置报文过滤，以此关闭规则匹配统计功能。

一个接口在一个方向上最多可应用4个ACL进行报文过滤，包括一个IPv4 ACL、一个IPv6 ACL、一个二层ACL以及一个用户自定义ACL。

基于二层聚合接口和三层聚合接口应用ACL进行报文过滤时，仅支持对接口收到的报文进行过滤。

仅Release 2510P01及以上版本支持对VSI虚接口收到的报文进行过滤。

【举例】

\# 应用IPv4基本ACL 2001对接口Ten-GigabitEthernet1/0/1收到的报文进行过滤，并对过滤的报文进行统计。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] packet-filter 2001 inbound hardware-count

【相关命令】

· display packet-filter

· display packet-filter statistics

· display packet-filter verbose


---

<!-- 08-ACL和QoS命令参考/html/-1076425793_1838026174_1900467657_67978721.htm -->

rule命令用来为二层ACL创建一条规则。

undo rule命令用来为二层ACL删除一条规则或删除规则中的部分内容。

【命令】

rule [ rule-id ] { deny | permit } [ cos dot1p | counting | dest-mac dest-address dest-mask | { lsap lsap-type lsap-type-mask | type protocol-type protocol-type-mask } | source-mac source-address source-mask | time-range time-range-name ] *

undo rule rule-id [ counting | time-range ] *

undo rule { deny | permit } [ cos dot1p | counting | dest-mac dest-address dest-mask | { lsap lsap-type lsap-type-mask | type protocol-type protocol-type-mask } | source-mac source-address source-mask | time-range time-range-name ] *

【缺省情况】

二层ACL内不存在任何规则。

【视图】

二层ACL视图

【缺省用户角色】

network-admin

【参数】

rule-id：指定二层ACL规则的编号，取值范围为0～65534。若未指定本参数，系统将从规则编号的起始值开始，自动分配一个大于现有最大编号的步长最小倍数。譬如现有规则的最大编号为28，步长为5，那么自动分配的新编号将是30。

deny：表示拒绝符合条件的报文。

permit：表示允许符合条件的报文。

cos dot1p：指定802.1p优先级。dot1p表示802.1p优先级，可输入的形式如下：

· 数字：取值范围为0～7；

· 名称：best-effort、background、spare、excellent-effort、controlled-load、video、voice和network-management，依次对应于数字0～7。

counting：表示开启规则匹配统计功能，缺省为关闭。

dest-mac dest-address dest-mask：指定目的MAC地址范围。dest-address表示目的MAC地址，格式为H-H-H。dest-mask表示目的MAC地址的掩码，格式为H-H-H。

lsap lsap-type lsap-type-mask：指定LLC封装中的DSAP字段和SSAP字段。lsap-type表示数据帧的封装格式，取值范围为十六进制数0～ffff。lsap-type-mask表示LSAP的类型掩码，用于指定屏蔽位，取值范围为十六进制数0～ffff。

type protocol-type protocol-type-mask：指定链路层协议类型。protocol-type表示数据帧类型，对应Ethernet_II类型和Ethernet_SNAP类型帧中的type域，取值范围为十六进制数0～ffff。protocol-type-mask表示类型掩码，用于指定屏蔽位，取值范围为十六进制数0～ffff。

source-mac source-address source-mask：指定源MAC地址范围。source-address表示源MAC地址，格式为H-H-H。source-mask表示源MAC地址的掩码，格式为H-H-H。

time-range time-range-name：指定本规则生效的时间段。time-range-name表示时间段的名称，为1～32个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。若该时间段尚未配置，该规则仍会成功创建但系统将给出提示信息，并在该时间段的配置完成后此规则才会生效。有关时间段的详细介绍和具体配置过程，请参见“ACL和QoS配置指导”中的“时间段”。

【使用指导】

使用rule命令时，如果指定编号的规则不存在，则创建一条新的规则；如果指定编号的规则已存在，则对旧规则进行修改，即在其原有内容的基础上叠加新的内容。

新创建或修改的规则不能与已有规则的内容完全相同，否则将提示出错，并导致该操作失败。

当ACL的规则匹配顺序为配置顺序时，允许修改该ACL内的任意一条已有规则；当ACL的规则匹配顺序为自动排序时，不允许修改该ACL内的已有规则，否则将提示出错。

display acl mac all命令可以查看所有已存在的二层ACL规则。

删除规则时请注意：

· 使用undo rule rule-id命令时，必须指定一个已存在规则的编号。

· 使用undo rule rule-id命令时，如果没有指定任何可选参数，则删除整条规则；如果指定了可选参数，则只删除该参数所对应的内容。

· undo rule { deny | permit }命令无法删除规则中的部分内容。使用undo rule { deny | permit }命令时，必须输入已存在规则的完整形式。

counting参数用于开启本规则的匹配统计功能，而packet-filter命令中的hardware-count参数则用于开启指定ACL内所有规则的匹配统计功能。

【举例】

\# 为二层ACL 4000创建规则如下：允许ARP报文通过，但拒绝RARP报文通过。

<Sysname> system-view

[Sysname] acl mac 4000

[Sysname-acl-mac-4000] rule permit type 0806 ffff

[Sysname-acl-mac-4000] rule deny type 8035 ffff

【相关命令】

· acl

· display acl

· step

· time-range（ACL和QoS命令参考/时间段）


---

<!-- 08-ACL和QoS命令参考/html/-160337002_-1300025618_-1324685525_-2103171170.htm -->

time-range命令用来创建一个时间段，来描述一个特定的时间范围。如果指定的时间段已经创建，则本命令可以修改时间段的时间范围。

undo time-range命令用来删除一个时间段。

【命令】

time-range time-range-name { start-time to end-time days [ from time1 date1 ] [ to time2 date2 ] | from time1 date1 [ to time2 date2 ] | to time2 date2 }

undo time-range time-range-name [ start-time to end-time days [ from time1 date1 ] [ to time2 date2 ] | from time1 date1 [ to time2 date2 ] | to time2 date2 ]

【缺省情况】

不存在时间段。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

time-range-name：指定时间段的名称，为1～32个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。为避免混淆，时间段的名称不允许使用英文单词all。

start-time to end-time：指定周期时间段的时间范围。start-time表示起始时间，格式为hh:mm，取值范围为00:00～23:59；end-time表示结束时间，格式为hh:mm，取值范围为00:00～24:00，且结束时间必须大于起始时间。

days：指定周期时间段在每周的周几生效。本参数可输入多次，但后输入的值不能与此前输入的值完全重叠（譬如输入6后不允许再输入Sat，但允许再输入off-day），系统将取各次输入值的并集作为最终值（譬如依次输入1、Wed和working-day之后，最终生效的时间将为每周的工作日）。本参数可输入的形式如下：

· 数字：取值范围为0～6，依次表示周日～周六；

· 周几的英文缩写（从周日到周六依次为Sun、Mon、Tue、Wed、Thu、Fri和Sat）；

· 工作日（working-day）：表示从周一到周五；

· 休息日（off-day）：表示周六和周日；

· 每日（daily）：表示一周七天。

from time1 date1：指定绝对时间段的起始时间。time1的格式为hh:mm，取值范围为00:00～23:59。date1的格式为MM/DD/YYYY或YYYY/MM/DD。MM表示月，取值范围为1～12；DD表示日，取值范围取决于所输入的月份；YYYY表示年，取值范围为1970～2100。若未指定本参数，绝对时间段的起始时间将为系统可表示的最早时间，即1970年1月1日0点0分。

to time2 date2：指定绝对时间段的结束时间。time2的格式为hh:mm，取值范围为00:00～24:00。date2的格式为MM/DD/YYYY或YYYY/MM/DD。MM表示月，取值范围为1～12；DD表示日，取值范围取决于所输入的月份；YYYY表示年，取值范围为1970～2100。结束时间必须大于起始时间。若未指定本参数，绝对时间段的结束时间将为系统可表示的最晚时间，即2100年12月31日24点0分。

【使用指导】

如果指定名称的时间段不存在，则创建一个新的时间段（最多1024个）；如果指定名称的时间段已存在，则对旧时间段进行修改，即在其原有内容的基础上叠加新的内容。

在一个时间段中，可以使用以下两种方式定义时间范围：

· 使用start-time to end-time days这组参数所创建的时间段为周期时间段，它将以一周为周期循环生效。

· 使用from time1 date1和to time2 date2这组参数所创建的时间段为绝对时间段，它将在指定时间范围内生效。

如果一个时间段中同时包含以上两种时间范围，将取周期时间段和绝对时间段的交集作为生效的时间范围。例如在一个时间段中定义周期时间段为每周一的8点到12点，定义绝对时间段为2015年全年，那么该时间段的生效时间范围为2015年全年内每周一的8点到12点。

一个时间段内可包含一或多个周期时间段（最多32个）和绝对时间段（最多12个），当包含有多个周期时间段和绝对时间段时，系统将先分别取各周期时间段的并集和各绝对时间段的并集，再取这两个并集的交集作为该时间段最终生效的时间范围。

【举例】

\# 创建名为t1的时间段，其时间范围为每周工作日的8点到18点。

<Sysname> system-view

[Sysname] time-range t1 08:00 to 18:00 working-day

\# 创建名为t2的时间段，其时间范围为2011年全年。

<Sysname> system-view

[Sysname] time-range t2 from 00:00 1/1/2011 to 24:00 12/31/2011

\# 创建名为t3的时间段，其时间范围为2011年全年内每周休息日的8点到12点。

<Sysname> system-view

[Sysname] time-range t3 08:00 to 12:00 off-day from 00:00 1/1/2011 to 24:00 12/31/2011

\# 创建名为t4的时间段，其时间范围为2011年1月和6月内每周一的10点到12点以及每周三的14到16点。

<Sysname> system-view

[Sysname] time-range t4 10:00 to 12:00 1 from 00:00 1/1/2011 to 24:00 1/31/2011

[Sysname] time-range t4 14:00 to 16:00 3 from 00:00 6/1/2011 to 24:00 6/30/2011

【相关命令】

· display time-range


---

<!-- 08-ACL和QoS命令参考/html/-160337002_-1300025618_-1324685525_-973786166.htm -->

display time-range命令用来显示时间段的配置和状态信息。

【命令】

display time-range { time-range-name | all }

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

time-range-name：显示指定名称时间段的配置和状态信息。time-range-name表示时间段的名称，为1～32个字符的字符串，不区分大小写，必须以英文字母a～z或A～Z开头。

all：显示所有时间段的配置和状态信息。

【举例】

\# 显示时间段t4的配置和状态信息。

<Sysname> display time-range t4

Current time is 17:12:34 11/23/2010 Tuesday

Time-range: t4 (Inactive)

 10:00 to 12:00 Mon

 14:00 to 16:00 Wed

 from 00:00 1/1/2011 to 00:00 1/1/2012

 from 00:00 6/1/2011 to 00:00 7/1/2011

表1-1 display time-range命令显示信息描述表

| Time-range | 时间段的配置信息，包括： · 时间段的名称 · 时间段的状态，包括Active（生效）和Inactive（未生效）两种状态 · 时间段的时间范围 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-1673314845.htm -->

display qos policy命令用来显示QoS策略的配置信息。

【命令】

display qos policy user-defined [ policy-name [ classifier classifier-name ] ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

user-defined：用户定义QoS策略。

policy-name：QoS策略名，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示所有用户定义策略的配置信息。

classifier classifier-name：QoS策略中的类名，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示策略中所有类相关的配置信息。

slot slot-number：显示指定成员设备的QoS策略的信息，slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主用设备的QoS策略的配置信息。

【举例】

\# 显示用户定义QoS策略的配置信息。

<Sysname> display qos policy user-defined

 User-defined QoS policy information:

 Policy: 1 (ID 100)

 Classifier: 1 (ID 100)

 Behavior: 1

 Marking:

 Remark dscp 3

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 512 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Classifier: 2 (ID 101)

 Behavior: 2

 Accounting enable: Packet

 Filter enable: Permit

 Marking:

 Remark dot1p 4

 Classifier: 3 (ID 102)

 Behavior: 3

 -none-

表1-6 display qos policy命令显示信息描述表

| Policy | QoS策略名 |
| --- | --- |

其它显示信息解释请参见表1-1和表1-4。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-1714745843.htm -->

display qos policy control-plane pre-defined命令用来显示系统预定义的控制平面应用QoS策略的信息。

【命令】

display qos policy control-plane pre-defined [ slot slot-number ]

【视图】

任意视图‌

【缺省用户角色】

network-admin

network-operator

【参数】

slot slot-number：显示指定成员设备的系统预定义的控制平面策略信息，slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示所有成员设备的系统预定义的控制平面应用QoS策略的信息。

【举例】

\# 显示指定slot上的系统预定义的控制平面应用QoS策略的信息。

<Sysname> display qos policy control-plane pre-defined slot 1

Pre-defined policy information slot 1

 Protocol Priority Bandwidth Group

 Default N/A 1000 (pps) N/A

 IS-IS 18 1000 (pps) critical

 VRRP 19 1000 (pps) important

 OSPF Multicast 18 1000 (pps) critical

 OSPF Unicast 18 1000 (pps) critical

 IGMP 11 500 (pps) important

 OSPFv3 Unicast 18 1000 (pps) critical

 OSPFv3 Multicast 18 1000 (pps) critical

 VRRPv6 19 1000 (pps) important

 ARP 2 1000 (pps) normal

 DHCP Snooping 10 300 (pps) redirect

 DHCP 10 300 (pps) normal

 802.1x 3 500 (pps) important

 STP 17 300 (pps) critical

 LACP 22 300 (pps) critical

 MVRP 15 300 (pps) critical

 BGP 16 1000 (pps) critical

 ICMP 3 500 (pps) monitor

 TTL Expires 5 300 (pps) monitor

 IPOPTION 5 300 (pps) normal

 BGPv6 16 1000 (pps) critical

 Hop Limit Expires 5 300 (pps) monitor

 IPOPTIONv6 5 300 (pps) normal

 LLDP 14 300 (pps) important

 DLDP 16 300 (pps) critical

 TELNET 1 800 (pps) management

 SSH 1 800 (pps) management

 TACACS 1 800 (pps) management

 RADIUS 1 800 (pps) management

 HTTP 3 500 (pps) management

 HTTPS 3 500 (pps) management

 SNMP 4 800 (pps) management

 ARP Snooping 2 1000 (pps) redirect

 ICMPv6 3 300 (pps) monitor

 DHCPv6 10 300 (pps) normal

 BFD 21 1000 (pps) critical

表1-8 display qos policy control-plane pre-defined命令显示信息描述表

| Group | 协议所属的协议组 |
| --- | --- |

其它显示信息解释请参见表1-3。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-1731348818.htm -->

reset qos vlan-policy命令用来清除VLAN应用的QoS策略的统计信息。

【命令】

reset qos vlan-policy [ vlan vlan-id ] [ inbound | outbound ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

vlan vlan-id：指定VLAN。vlan-id为指定VLAN的ID号，取值范围为1～4094。

inbound：清除VLAN接收到的报文应用QoS策略的统计信息。

outbound：清除对VLAN发送的报文应用QoS策略的统计信息。

【使用指导】

如果不指定方向，则同时清除出入两个方向VLAN应用的QoS策略的统计信息。

【举例】

\# 清除VLAN 2应用的QoS策略的统计信息。

<Sysname> reset qos vlan-policy vlan 2


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-1900794048.htm -->

display qos policy global命令用来显示基于全局应用QoS策略的信息。

【命令】

display qos policy global [ slot slot-number ] [ inbound | outbound ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

inbound：显示对全局接收到的报文应用QoS策略的信息。

outbound：显示对全局发送的报文应用QoS策略的信息。

slot slot-number：显示指定成员设备的基于全局应用QoS策略的信息，slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主设备上基于全局应用QoS策略的信息，不显示各成员设备的信息。

【使用指导】

如果未指定显示方向，则同时显示出入两个方向基于全局应用QoS策略的信息。

【举例】

\# 显示基于全局应用QoS策略的信息。

<Sysname> display qos policy global

 Direction: Inbound

 Policy: 1

 Classifier: 1

 Operator: AND

 Rule(s):

 If-match acl 2000

 Behavior: 1

 Marking:

 Remark dscp 3

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 512 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0 (Packets) 0 (Bytes)

 Yellow packets: 0 (Packets) 0 (Bytes)

 Red packets: 0 (Packets) 0 (Bytes)

 Classifier: 2

 Operator: AND

 Rule(s):

 If-match protocol ipv6

 Behavior: 2

 Accounting enable:

 0 (Packets)

 Filter enable: Permit

 Marking:

 Remark dscp 3

 Classifier: 3

 Operator: AND

 Rule(s):

 -none-

 Behavior: 3

 -none-

表1-9 display qos policy global命令显示信息描述表

| Red packets | 红色报文的流量统计 |
| --- | --- |

其它显示信息解释请参见表1-1和表1-4。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-2015665687.htm -->

qos apply policy命令用来在接口、控制平面上应用QoS策略。

undo qos apply policy命令用来取消接口、控制平面上应用的QoS策略。

【命令】

qos apply policy policy-name { inbound | outbound }

undo qos apply policy policy-name { inbound | outbound }

【缺省情况】

未应用QoS策略。

【视图】

二层以太网接口视图/二层聚合接口视图/三层以太网接口视图/三层以太网子接口视图/三层以太网聚合接口视图/控制平面视图

【缺省用户角色】

network-admin

【参数】

policy-name：策略名，为1～31个字符的字符串，区分大小写。

inbound：对接口或控制平面接收到的报文应用QoS策略。

outbound：对接口发送的报文应用QoS策略。

【使用指导】

在控制平面应用QoS策略时，如果流分类的匹配条件是control-plane protocol-group或control-plane protocol，则流行为的动作只能为car，或者car和accounting packet动作的组合，且在car动作中只有cir参数的取值可以被正常应用。

设备仅支持对二层聚合接口和三层聚合接口接收到的报文应用QoS策略。

【举例】

\# 将策略USER1应用到接口Ten-GigabitEthernet1/0/1的出方向上。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos apply policy USER1 outbound

\# 对进入3号槽控制平面的报文应用策略aaa。

<Sysname> system-view

[Sysname] control-plane slot 3

[Sysname-cp-slot3] qos apply policy aaa inbound


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-51069600.htm -->

reset qos policy global命令用来清除全局应用的QoS策略的统计信息。

【命令】

reset qos policy global [ inbound | outbound ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

inbound：清除全局接收到的报文应用QoS策略的统计信息。

outbound：清除全局发送的报文应用QoS策略的统计信息。

【使用指导】

如果不指定方向，则同时清除出入两个方向全局应用的QoS策略的统计信息。

【举例】

\# 清除全局入方向应用的QoS策略的统计信息。

<Sysname> reset qos policy global inbound


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-835851566.htm -->

display qos policy interface命令用来显示接口上QoS策略的配置信息和运行情况。

【命令】

display qos policy interface [ interface-type interface-number ] [ slot slot-number ] [ inbound | outbound ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口上QoS策略的配置信息和运行情况。

slot slot-number：显示指定成员设备指定接口的QoS策略的配置信息和运行情况。slot-number表示设备在IRF中的成员编号。只有当接口为VLAN虚接口、聚合口等类型时才支持此参数。

inbound：显示对接口接收到的报文应用QoS策略的信息。

outbound：显示对接口发送的报文应用QoS策略的信息。

【使用指导】

如果未指定显示方向，则同时显示出入两个方向接口上应用QoS策略的配置信息和运行情况。

【举例】

\# 显示对接口Ten-GigabitEthernet1/0/1接收到的报文应用QoS策略的配置信息和运行情况。

<Sysname> display qos policy interface ten-gigabitethernet 1/0/1 inbound

Interface: Ten-GigabitEthernet1/0/1

 Direction: Inbound

 Policy: 1

 Classifier: 1

 Matched: 0 (Packets) 0 (Bytes)

 5-minute statistics:

 Forwarded: 0/0 (pps/bps)

 Dropped: 0/0 (pps/bps)

 Operator: AND

 Rule(s):

 If-match acl 2000

 Behavior: 1

 Marking:

 Remark dscp 3

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 512 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0 (Packets) 0 (Bytes)

 Yellow packets: 0 (Packets) 0 (Bytes)

 Red packets: 0 (Packets) 0 (Bytes)

 Classifier: 2

 Matched: 0 (Packets) 0 (Bytes)

 5-minute statistics:

 Forwarded: 0/0 (pps/bps)

 Dropped: 0/0 (pps/bps)

 Operator: AND

 Rule(s):

 If-match protocol ipv6

 Behavior: 2

 Accounting enable:

 0 (Packets)

 Filter enable: Permit

 Marking:

 Remark dscp 3

 Classifier: 3

 Matched: 0 (Packets) 0 (Bytes)

 5-minute statistics:

 Forwarded: 0/0 (pps/bps)

 Dropped: 0/0 (pps/bps)

 Operator: AND

 Rule(s):

 -none-

 Behavior: 3

 -none-

\# 显示所有接口上QoS策略的接口的配置信息和运行情况。

<Sysname> display qos policy interface

Interface: Ten-GigabitEthernet1/0/1

 Direction: Inbound

 Policy: a

 Classifier: a

 Operator: AND

 Rule(s):

 If-match any

 Behavior: a

 Mirroring:

 Mirror to the interface: Ten-GigabitEthernet1/0/2

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 0 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0 (Packets)

 Red packets: 0 (Packets)

Interface: Ten-GigabitEthernet1/0/3

 Direction: Inbound

 Policy: b

 Classifier: b

 Operator: AND

 Rule(s):

 If-match any

 Behavior: b

 Committed Access Rate:

 CIR 200 (kbps), CBS 51200 (Bytes), EBS 0 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0(Packets)

 Red packets: 0 (Packets)

Interface: Ten-GigabitEthernet1/0/3

 Direction: Inbound

 Policy: a

 Classifier: a

 Operator: AND

 Rule(s):

 If-match any

 Behavior: a

 Mirroring:

 Mirror to the interface: Ten-GigabitEthernet1/0/4

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 0 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0 (Packets)

 Red packets: 0 (Packets)

表1-10 display qos policy interface命令显示信息描述表

| Red packets | 红色报文的流量统计 |
| --- | --- |

其它显示信息解释请参见表1-1和表1-4。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_-987467756.htm -->

qos policy命令用来创建一个策略，并进入策略视图。如果指定的策略已经存在，则直接进入策略视图。

undo qos policy命令用来删除一个策略。

【命令】

qos policy policy-name

undo qos policy policy-name

【缺省情况】

不存在策略。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

policy-name：策略名，为1～31个字符的字符串，区分大小写。

【使用指导】

如果该策略已经被应用，则不允许删除该策略，需要先在应用的位置上取消对该策略的应用，然后再使用undo qos policy命令删除该策略。

【举例】

\# 定义一个名为user1的策略。

<Sysname> system-view

[Sysname] qos policy user1

[Sysname-qospolicy-user1]

【相关命令】

· classifier behavior

· qos apply policy

· qos apply policy global

· qos vlan-policy


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_1226080449.htm -->

reset qos policy control-plane命令用来清除控制平面应用QoS策略的统计信息。

【命令】

reset qos policy control-plane slot slot-number

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

slot slot-number：清除指定成员设备的基于控制平面应用QoS策略的统计信息，slot-number表示设备在IRF中的成员编号。

【举例】

\# 清除应用到指定slot上的控制平面的QoS策略统计信息。

<Sysname> reset qos policy control-plane slot 3


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_1271849171.htm -->

classifier behavior命令用来为类指定流行为。

undo classifier命令用来取消为类指定的流行为。

【命令】

classifier classifier-name behavior behavior-name [ insert-before before-classifier-name ]

undo classifier classifier-name

【缺省情况】

没有为类指定流行为。

【视图】

QoS策略视图

【缺省用户角色】

network-admin

【参数】

classifier-name：类名，为1～31个字符的字符串，区分大小写。

behavior-name：流行为名，为1～31个字符的字符串，区分大小写。

insert-before before-classifier-name：表示将配置的类插入到QoS策略中已存在的指定类之前。before-classifier-name表示QoS策略中已存在的类名，为1～31个字符的字符串，区分大小写。不指定该参数时，表示新配置的类与流行为配对将添加到QoS策略最后。

【使用指导】

QoS策略下每个类只能与一个流行为关联。

如果配置本命令时指定的类和流行为不存在，系统将创建一个空的类和空的流行为。

【举例】

\# 在QoS策略user1中为类database指定采用流行为test。

<Sysname> system-view

[Sysname] qos policy user1

[Sysname-qospolicy-user1] classifier database behavior test

\# 在QoS策略user1中为类database指定流行为test，并将该类插入到策略中已存在的类class-a前。

<Sysname> system-view

[Sysname] qos policy user1

[Sysname-qospolicy-user1] classifier database behavior test insert-before class-a

【相关命令】

· qos policy


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_1715828959.htm -->

qos apply policy global命令用来全局应用QoS策略。

undo qos apply policy global命令用来取消全局应用的QoS策略。

【命令】

qos apply policy policy-name global { inbound | outbound }

undo qos apply policy policy-name global { inbound | outbound }

【缺省情况】

未在全局应用QoS策略。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

policy-name：策略名，为1～31个字符的字符串，区分大小写。

inbound：对设备所有端口接收到的流量应用QoS策略。

outbound：对设备所有端口发送的流量应用QoS策略。

【使用指导】

全局应用的QoS策略对全部流量生效。

【举例】

\# 将名为user1的策略应用到全局的入方向上。

<Sysname> system-view

[Sysname] qos apply policy user1 global inbound


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_1906071670.htm -->

qos apply policy命令用来在User Profile下应用策略。

undo qos apply policy命令用来取消User Profile下应用的策略。

【命令】

qos apply policy policy-name { inbound | outbound }

undo qos apply policy policy-name { inbound | outbound }

【缺省情况】

未在User Profile下应用QoS策略。

【视图】

User Profile视图

【缺省用户角色】

network-admin

【参数】

inbound：入方向，对设备接收的上线用户流量（即上线用户发送的流量）应用策略。

outbound：出方向，对设备发送的上线用户流量（即上线用户接收的流量）应用策略。

policy-name：策略名，为1～31个字符的字符串。

【使用指导】

User Profile被删除将导致其下引用的QoS策略被删除。

如果QoS策略的流行为视图下配置了重定向到接口，则User Profile下应用该策略只能应用到入方向。

【举例】

\# 对设备发送的上线用户user的流量应用策略test（该策略已经建立）。

<Sysname> system-view

[Sysname] user-profile user

[Sysname-user-profile-user] qos apply policy test outbound


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_2056995505.htm -->

display qos vlan-policy命令用来显示基于VLAN应用QoS策略的信息。

【命令】

display qos vlan-policy { name policy-name | vlan [ vlan-id ] } [ slot slot-number ] [ inbound | outbound ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

name policy-name：显示指定策略名称的基于VLAN应用QoS策略的信息。policy-name表示策略名称，为1～31个字符的字符串，区分大小写。

vlan vlan-id：显示指定VLAN上应用QoS策略的信息。vlan-id为指定VLAN的ID号，取值范围为1～4094。

inbound：显示对VLAN接收到的报文应用的QoS策略信息。

outbound：显示对VLAN发送的报文应用的QoS策略信息。

slot slot-number：显示指定成员设备上基于VLAN应用QoS策略的信息，slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主设备上基于VLAN应用QoS策略的信息。

【使用指导】

如果未指定显示方向，则同时显示出入两个方向基于VLAN应用QoS策略的信息。

【举例】

\# 显示VLAN 2的QoS策略信息。

<Sysname> display qos vlan-policy vlan 2

Vlan 2

 Direction: Outbound

 Policy: 1

 Classifier: 1

 Operator: AND

 Rule(s):

 If-match acl 2000

 Behavior: 1

 Marking:

 Remark dscp 3

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 512 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0(Packets) 0(Bytes)

 Yellow packets: 0(Packets) 0(Bytes)

 Red packets: 0(Packets) 0(Bytes)

 Classifier: 2

 Operator: AND

 Rule(s):

 If-match protocol ipv6

 Behavior: 2

 Accounting enable:

 0 (Packets)

 Filter enable: Permit

 Marking:

 Remark dscp 3

 Classifier: 3

 Operator: AND

 Rule(s):

 -none-

 Behavior: 3

 -none-

表1-12 display qos vlan-policy命令显示信息描述表

| Red packets | 红色报文的流量统计 |
| --- | --- |

其它显示信息解释请参见表1-1和表1-4。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_2087930645.htm -->

qos vlan-policy命令用来在VLAN上应用QoS策略。

undo qos vlan-policy命令用来取消VLAN上应用的QoS策略。

【命令】

qos vlan-policy policy-name vlan vlan-id-list { inbound | outbound }

undo qos vlan-policy policy-name vlan vlan-id-list { inbound | outbound }

【缺省情况】

未在VLAN上应用QoS策略。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

policy-name：策略名称，为1～31个字符的字符串，区分大小写。

vlan-id-list：VLAN ID列表，形式可以是vlan-id to vlan-id，其中，vlan-id为指定VLAN的ID号，取值范围为1～4094。可以输入多个不连续的VLAN ID，中间以空格隔开。设备最多允许用户同时指定8个VLAN ID。

inbound：对VLAN接收到的报文应用QoS策略。

outbound：对VLAN发送的报文应用QoS策略。

【举例】

\# 在VLAN 200、300、400、500的入方向上应用策略test。

<Sysname> system-view

[Sysname] qos vlan-policy test vlan 200 300 400 500 inbound


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_276974587.htm -->

display qos policy control-plane命令用来显示控制平面应用QoS策略的信息。

【命令】

display qos policy control-plane slot slot-number

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

slot slot-number：显示指定成员设备的控制平面应用QoS策略的信息，slot-number表示设备在IRF中的成员编号。

【举例】

\# 显示应用到指定slot上的控制平面的QoS策略信息。

<Sysname> display qos policy control-plane slot 2

Control plane slot 2

 Direction: Inbound

 Policy: 1

 Classifier: 1

 Operator: AND

 Rule(s):

 If-match acl 2000

 Behavior: 1

 Marking:

 Remark dscp 3

 Committed Access Rate:

 CIR 112 (kbps), CBS 5120 (Bytes), EBS 512 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Green packets: 0 (Packets) 0 (Bytes)

 Yellow packets: 0 (Packets) 0 (Bytes)

 Red packets: 0 (Packets) 0 (Bytes)

 Classifier: 2

 Operator: AND

 Rule(s):

 If-match protocol ipv6

 Behavior: 2

 Accounting enable:

 0 (Packets)

 Filter enable: Permit

 Marking:

 Remark dscp 3

 Classifier: 3

 Operator: AND

 Rule(s):

 -none-

 Behavior: 3

 -none-

表1-7 display qos policy control-plane命令显示信息描述表

| Red packets | 红色报文的流量统计 |
| --- | --- |

其它显示信息解释请参见表1-6。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_384968748.htm -->

control-plane命令用来进入控制平面视图。

【命令】

control-plane slot slot-number

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

slot slot-number：指定成员设备。slot-number表示设备在IRF中的成员编号。

【举例】

\# 进入指定slot上的控制平面视图。

<Sysname> system-view

[Sysname] control-plane slot 3

[Sysname-cp-slot3]


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_1025388620_493643143.htm -->

display qos policy user-profile命令用来显示用户上线后User Profile下应用的QoS策略的信息和运行情况。

【命令】

display qos policy user-profile [ name profile-name ] [ user-id user-id ] [ slot slot-number ] [ inbound | outbound ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

name profile-name：指定User Profile的名称，为1～31个字符的字符串，只能包含英文字母[a-z,A-Z]、数字、下划线，且必须以英文字母开始，区分大小写。User Profile的名称必须全局唯一。如果未指定本参数，将显示所有User Profile下应用的QoS策略的信息和运行情况。

user-id user-id：表示在线用户的ID，为系统所分配，取值范围为十六进制数0～fffffffe。若未指定本参数，则显示所有用户在User Profile下应用的QoS策略的信息和运行情况。

slot slot-number：显示指定成员设备上指定用户在User Profile下应用的QoS策略的信息和运行情况，slot-number表示设备在IRF中的成员编号。如果未指定本参数，将显示所有成员设备上的在线用户上指定用户在User Profile下应用的QoS策略的信息和运行情况。

inbound：显示在线用户在入方向上应用QoS策略的信息。

outbound：显示在线用户在出方向上应用QoS策略的信息。

【使用指导】

如果未指定显示方向，则同时显示出入两个方向上应用QoS策略的配置信息和运行情况。

【举例】

\# 显示指定全局用户（从聚合口等全局口上线的用户）在User Profile下应用QoS策略的配置信息和运行情况。

<Sysname> display qos policy user-profile name abc user-id 30000000 inbound

User-Profile: abc

 User ID: 0x30000000(global)

 Direction: Inbound

 Policy: p1

 Classifier: default-class

 Matched: 0 (Packets) 0 (Bytes)

 Operator: AND

 Rule(s):

 If-match any

 Behavior: be

 -none-

\# 显示指定的非全局用户在User Profile下应用QoS策略的配置信息和运行情况。

<Sysname> display qos policy user-profile name abc user-id 30000001 inbound

User-Profile: abc

 slot 2:

 User ID: 0x30000001(local)

 Direction: Inbound

 Policy: p1

 Classifier: default-class

 Matched: 0 (Packets) 0 (Bytes)

 Operator: AND

 Rule(s):

 If-match any

 Behavior: be

 -none-

表1-11 display qos policy user-profile命令显示信息描述表

| Red packets | 红色报文的流量统计 |
| --- | --- |

其它显示信息解释请参见表1-1和表1-4。


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_511427645_-1596857994.htm -->

display traffic classifier命令用来显示类的配置信息。

【命令】

display traffic classifier user-defined [ classifier-name ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

user-defined：用户定义类。

classifier-name：类名，为1～31个字符的字符串，区分大小写。如果未指定本参数，将显示所有类的配置信息。

slot slot-number：显示指定成员设备的流分类的信息，slot-number表示设备在IRF中的成员编号。如果未指定本参数，将显示主用设备的类的配置信息。

【举例】

\# 显示用户定义类的配置信息。

<Sysname> display traffic classifier user-defined

 User-defined classifier information:

 Classifier: 1 (ID 100)

 Operator: AND

 Rule(s):

 If-match acl 2000

 Classifier: 2 (ID 101)

 Operator: AND

 Rule(s):

 If-match protocol ipv6

 Classifier: 3 (ID 102)

 Operator: AND

 Rule(s):

 -none-

表1-1 display traffic classifier命令显示信息描述表

| Rule(s) | 分类规则 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_511427645_-1904213270.htm -->

if-match命令用来定义匹配数据包的规则。

undo if-match命令用来删除配置的匹配数据包的规则。

【命令】

if-match match-criteria

undo if-match match-criteria

【缺省情况】

未定义匹配数据包的规则。

【视图】

类视图

【缺省用户角色】

network-admin

【参数】

match-criteria：类的匹配规则，具体情况如[表1-2](#_Ref213127397)所示。

表1-2 类的匹配规则取值

| vxlan { any \| vxlan-id } | 定义匹配VXLAN编号的规则 在入方向仅支持匹配VTEP收到的VXLAN报文 在出方向支持匹配： · VTEP发送给对端VTEP的VXLAN报文； · VTEP解封装后发送给用户终端的报文； 出方向匹配报文时需要注意的是，规则中的vxlan-id应为VSI Index值，例如VXLAN 10对应VSI A，VSI A对应的VSI Index为0，if-match vxlan 10不能匹配出方向VSI A中的报文，必须通过if-match vxlan 0匹配VSI A中的报文，可以通过display l2vpn vsi命令查看vxlan-id、VSI名称和VSI Index的对应关系，关于该命令的详细介绍，请参见“VXLAN命令参考” |
| --- | --- |

‌

表1-3 系统预定义匹配协议报文类型名称的列表

| vrrp6 | IPv6 VRRP协议 |
| --- | --- |

‌

【使用指导】

一个类下可配置多条匹配命令，各个配置之间互相不覆盖。

在定义匹配规则（控制平面、DSCP、VLAN ID、802.1p优先级、IP优先级）时，请注意：

· 一条命令可以配置多个规则，如果指定了多个相同的规则，系统默认为一个；一条命令中多个不同的规则是或的关系，即只要有一个值匹配，就算匹配这条规则。

· 删除某条匹配的规则时，必须与该规则中定义的完全相同才会删除，顺序可以不同。

在定义匹配ACL的规则时，请注意：

· 如果类中引用的ACL不存在，则不能在硬件中下发。

· 对同一个类，允许通过ACL名称和序号的方式分别引用一次同一个ACL。

当if-match中引用的ACL规则的动作为deny时，则直接忽略ACL规则的动作，以流行为中定义的动作为准，报文匹配只使用ACL中的分类域。

在定义匹配类的规则时，如果匹配类的规则之间既有逻辑与，又有逻辑或的关系，请使用以下方式配置。例如，需要定义classA，满足以下关系：规则1 & 规则2 | 规则3，可以这样定义：

· traffic classifier classB operator and

¡ if-match规则1

¡ if-match规则2

· traffic classifier classA operator or

¡ if-match规则3

【举例】

\# 定义类class1的匹配规则为：匹配目的MAC地址为0050-ba27-bed3的报文。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match destination-mac 0050-ba27-bed3

\# 定义类class2的匹配规则为：匹配源MAC地址为0050-ba27-bed2的报文。

<Sysname> system-view

[Sysname] traffic classifier class2

[Sysname-classifier-class2] if-match source-mac 0050-ba27-bed2

\# 定义类class1的匹配规则为：匹配内层VLAN Tag的802.1p优先级为3。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match customer-dot1p 3

\# 定义类class1的匹配规则为：匹配外层VLAN Tag的802.1p优先级为5。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match service-dot1p 5

\# 定义类匹配ACL3101。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match acl 3101

\# 定义类匹配ACL flow。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match acl name flow

\# 定义类匹配IPv6 ACL3101。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match acl ipv6 3101

\# 定义类匹配IPv6 ACL flow。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match acl ipv6 name flow

\# 定义匹配所有数据包的规则。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match any

\# 定义类class1的匹配规则为：匹配DSCP值为1或6或9的报文。

<Sysname> system-view

[Sysname] traffic classifier class1 operator or

[Sysname-classifier-class1] if-match dscp 1 6 9

\# 定义类class1的匹配规则为：匹配IP优先级值为1或6的报文。

<Sysname> system-view

[Sysname] traffic classifier class1 operator or

[Sysname-classifier-class1] if-match ip-precedence 1 6

\# 定义类匹配IP协议的报文。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match protocol ip

\# 定义类class1的匹配规则为：匹配内层VLAN Tag的VLAN ID值为1或6或9的报文。

<Sysname> system-view

[Sysname] traffic classifier class1 operator or

[Sysname-classifier-class1] if-match customer-vlan-id 1 6 9

\# 定义类class1的匹配规则为：匹配外层VLAN Tag的VLAN ID值为2或7或10的报文。

<Sysname> system-view

[Sysname] traffic classifier class1 operator or

[Sysname-classifier-class1] if-match service-vlan-id 2 7 10

\# 定义类class1匹配qos-local-id 3。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match qos-local-id 3

\# 在流分类class1中配置匹配上送控制平面的ARP协议报文。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match control-plane protocol arp

\# 在流分类class1中配置匹配上送控制平面的normal协议组报文。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match control-plane protocol-group normal

\# 在流分类class1中定义匹配隧道编号为2的VXLAN隧道中的所有VXLAN报文。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match tunnel-id 2

\# 定义类class1的匹配规则为：匹配VXLAN编号为10的报文。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1] if-match vxlan 10


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_511427645_287112946.htm -->

traffic classifier命令用来创建一个类，并进入类视图。如果指定的类已经存在，则直接进入类视图。

undo traffic classifier命令用来删除一个类。

【命令】

traffic classifier classifier-name [ operator { and | or } ]

undo traffic classifier classifier-name

【缺省情况】

不存在类。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

classifier-name：类名，为1～31个字符的字符串，区分大小写。

operator：指定各规则之间的逻辑运算符。缺省情况为and。

and：指定类下的规则之间是逻辑与的关系，即数据包必须匹配全部规则才属于该类。

or：指定类下的规则之间是逻辑或的关系，即数据包只要匹配其中任何一个规则就属于该类。

【举例】

\# 定义一个名为class1的类。

<Sysname> system-view

[Sysname] traffic classifier class1

[Sysname-classifier-class1]

【相关命令】

· display traffic classifier


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-114589891.htm -->

nest top-most命令用来添加报文的外层VLAN Tag。

undo nest top-most命令用来恢复缺省情况。

【命令】

nest top-most vlan vlan-id

undo nest top-most

【缺省情况】

未添加报文外层VLAN Tag。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

vlan vlan-id：添加的VLAN ID，取值范围为1～4094。

【使用指导】

引用了添加VLAN Tag动作的QoS策略只能应用到接口的入方向上。

在同一个流行为中多次执行本命令，最后一次执行的命令生效。

【举例】

\# 在流行为b1上配置如下动作：添加VLAN ID为123的VLAN Tag。

<Sysname> system-view

[Sysname] traffic behavior b1

[Sysname-behavior-b1] nest top-most vlan 123


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-1366038027.htm -->

remark local-precedence命令用来重新标记报文的本地优先级。

undo remark local-precedence命令用来取消标记报文的本地优先级。

【命令】

remark [ green | red | yellow ] local-precedence local-precedence-value

undo remark [ green | red | yellow ] local-precedence

【缺省情况】

未配置重新标记报文本地优先级的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

green：对绿色报文进行重标记。

red：对红色报文进行重标记。

yellow：对黄色报文进行重标记。

local-precedence-value：本地优先级，取值范围为0～7。

【举例】

\# 重新标记报文的本地优先级值为2。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark local-precedence 2


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-1475547132.htm -->

remark dot1p命令用来配置重新标记报文的802.1p优先级或内外层标签802.1p优先级复制动作。

undo remark dot1p命令用来恢复缺省情况。

【命令】

remark [ green | red | yellow ] dot1p dot1p-value

undo remark [ green | red | yellow ] dot1p

remark dot1p customer-dot1p-trust

undo remark dot1p

【缺省情况】

未配置重新标记报文802.1p优先级以及内外层标签802.1p优先级复制动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

green：对绿色报文进行重标记。

red：对红色报文进行重标记。

yellow：对黄色报文进行重标记。

dot1p-value：802.1p优先级，取值范围为0～7。

customer-dot1p-trust：将内层VLAN tag的802.1p优先级复制为外层VLAN tag的802.1p优先级。

【使用指导】

命令remark dot1p dot1p-value和remark dot1p customer-dot1p-trust是覆盖关系。

对于只携带一层VLAN tag的报文，配置的remark dot1p customer-dot1p-trust不会生效。

在同一个流行为中，如果多次对同一种颜色的报文重新标记802.1p优先级，则最后一次执行的命令生效。

【举例】

\# 重新标记报文的802.1p优先级值为2。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark dot1p 2

\# 配置内外层标签优先级复制功能。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark dot1p customer-dot1p-trust


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-1717592927.htm -->

redirect命令用来为流行为配置流量重定向动作。

undo redirect命令用来恢复缺省情况。

【命令】

redirect { cpu | interface interface-type interface-number }

undo redirect { cpu | interface interface-type interface-number }

【缺省情况】

未配置流量重定向动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

cpu：重定向到CPU。

interface：重定向到指定的接口。

interface-type interface-number：指定接口类型和接口编号。

slot slot-number：重定向到指定成员设备，slot-number表示设备在IRF中的成员编号。

【使用指导】

在同一个流行为中多次执行本命令，最后一次执行的命令生效。

通过QoS策略方式配置重定向时，仅支持应用在入方向。

基于上线用户应用QoS策略时，如果配置重定向到接口，则需确保redirect命令中指定的接口与重定向报文进入设备的接口属于同一VLAN。

【举例】

\# 为流行为配置流量重定向动作，重定向到接口Ten-GigabitEthernet1/0/1。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] redirect interface ten-gigabitethernet 1/0/1

【相关命令】

· classifier behavior

· qos policy

· traffic behavior


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-2000809967.htm -->

display traffic behavior命令用来显示流行为的配置信息。

【命令】

display traffic behavior user-defined [ behavior-name ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

user-defined：用户定义行为。

behavior-name：行为名，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示所有流行为的配置信息。

slot slot-number：显示指定成员设备的流行为的信息，slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主用设备的流行为的配置信息。

【举例】

\# 显示用户定义行为的配置信息。

<Sysname> display traffic behavior user-defined

 User-defined behavior information:

 Behavior: 1 (ID 100)

 Marking:

 Remark dscp 3

 Committed Access Rate:

 CIR 200 (kbps), CBS 51200 (Bytes), EBS 512 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Behavior: 2 (ID 101)

 Accounting enable: Packet

 Filter enable: Permit

 Marking:

 Remark dscp 4

 Redirecting:

 Redirect to the CPU

表1-4 display traffic behavior命令显示信息描述表

| Pre | 报文的IP优先级 |
| --- | --- |

‌


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-510180736.htm -->

remark customer-vlan-id命令用来重标记报文的CVLAN。

undo remark customer-vlan-id命令用来恢复缺省情况。

【命令】

remark customer-vlan-id vlan-id

undo remark customer-vlan-id

【缺省情况】

未配置重新标记报文的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

vlan-id：表示重标记报文内层VLAN（CVLAN）的编号，取值范围为1～4094。

【举例】

\# 在流行为b1上配置重标记报文的CVLAN为VLAN 111。

<Sysname> system-view

[Sysname] traffic behavior b1

[Sysname-behavior-b1] remark customer-vlan-id 111


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-543079069.htm -->

remark ip-precedence命令用来重新标记报文的IP优先级。

undo remark ip-precedence命令用来取消标记报文的IP优先级。

【命令】

remark [ green | red | yellow ] ip-precedence ip-precedence-value

undo remark [ green | red | yellow ] ip-precedence

【缺省情况】

未配置重新标记报文IP优先级的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

green：对绿色报文进行重标记。

red：对红色报文进行重标记。

yellow：对黄色报文进行重标记。

ip-precedence-value：IP优先级，取值范围为0～7。

【举例】

\# 重新标记报文的IP优先级值为6。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark ip-precedence 6


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_-60967688.htm -->

remark drop-precedence命令用来重新标记报文的丢弃优先级。

undo remark drop-precedence命令用来恢复缺省情况。

【命令】

remark drop-precedence drop-precedence-value

undo remark drop-precedence

【缺省情况】

未配置重新标记报文的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

drop-precedence-value：丢弃优先级，取值范围为0～2。

【使用指导】

应用该动作的流行为只能应用在入方向。

在同一个流行为中多次执行本命令，最后一次执行的命令生效。

【举例】

\# 重新标记报文的丢弃优先级值为2。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark drop-precedence 2


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_1086985219.htm -->

remark qos-local-id命令用来重新标记报文的QoS本地ID值。

undo remark qos-local-id命令用来恢复缺省情况。

【命令】

remark qos-local-id local-id-value

undo remark qos-local-id

【缺省情况】

未配置重新标记报文的QoS本地ID值的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

local-id-value：QoS本地ID值，取值范围为1～4095。本系列交换机实际生效的取值范围为1～3999。

【使用指导】

一般情况下，在QoS策略的入方向对报文的QoS本地ID值进行标记，在QoS策略的出方向根据标记的QoS本地ID值对报文进行分类以及指定相应的流行为，两者要结合使用。

在IRF组网中，如果通过QoS策略重标记成员设备收到报文的QoS本地ID值，则在另一成员设备的接口出方向上无法通过QoS本地ID值匹配该报文。

在VXLAN组网中，如果通过QoS策略重标记VTEP设备或VXLAN IP网关收到报文的QoS本地ID值，则在对端VXLAN IP网关或VTEP设备的接口出方向上无法通过QoS本地ID值匹配该报文。

在同一个流行为中多次执行本命令，最后一次执行的命令生效。

【举例】

\# 重新标记报文的QoS本地ID值为2。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark qos-local-id 2


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_1628941772.htm -->

remark dscp命令用来重新标记报文的DSCP值。

undo remark dscp命令用来取消标记报文的DSCP值。

【命令】

remark [ green | red | yellow ] dscp dscp-value

undo remark [ green | red | yellow ] dscp

【缺省情况】

未配置重新标记报文DSCP值的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

green：对绿色报文进行重标记。

red：对红色报文进行重标记。

yellow：对黄色报文进行重标记。

dscp-value：DSCP值，取值范围为0～63，也可以是关键字，如[表1-5](#_Ref163816081)所示。

表1-5 DSCP关键字与值的对应表

| ef | 101110 | 46 |
| --- | --- | --- |

【举例】

\# 重新标记报文的DSCP值为6。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] remark dscp 6


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_327368249.htm -->

accounting命令用来配置流量统计动作。

undo accounting命令用来恢复缺省情况。

【命令】

accounting { byte | packet }

undo accounting

【缺省情况】

未配置流量统计动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

byte：表示报文基于字节进行统计。

packet：表示报文基于包进行统计。

【举例】

\# 为流行为配置流量统计动作，基于字节进行统计。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] accounting byte


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_40178284.htm -->

traffic behavior命令用来创建一个流行为，并进入流行为视图。如果指定的流行为已经存在，则直接进入流行为视图。

undo traffic behavior命令用来删除一个流行为。

【命令】

traffic behavior behavior-name

undo traffic behavior behavior-name

【缺省情况】

不存在流行为。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

behavior-name：流行为名，为1～31个字符的字符串，区分大小写。

【举例】

\# 定义一个名为behavior1的流行为。

<Sysname> system-view

[Sysname] traffic behavior behavior1

[Sysname-behavior-behavior1]

【相关命令】

· display traffic behavior


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_487884048.htm -->

filter命令用来配置流量过滤动作。

undo filter命令用来恢复缺省情况。

【命令】

filter { deny | permit }

undo filter

【缺省情况】

未配置流量过滤动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

deny：丢弃数据包。

permit：允许数据包通过。

【举例】

\# 为流行为配置丢弃数据包的过滤动作。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] filter deny


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_752713090.htm -->

car命令用来配置流量监管动作。

undo car命令用来恢复缺省情况。

【命令】

car cir [ pps ] committed-information-rate [ cbs committed-burst-size [ ebs excess-burst-size ] ] [ green action | red action | yellow action ] *

car cir [ pps ] committed-information-rate [ cbs committed-burst-size ] pir [ pps ] peak-information-rate [ ebs excess-burst-size ] [ green action | red action | yellow action ] *

undo car

【缺省情况】

未配置流量监管动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

cir committed-information-rate：承诺信息速率。流量的平均速率，不指定pps关键字时单位为kbps，指定pps关键字时单位为pps。取值范围为8～160000000且必须为8的整数倍。

cbs committee-burst-size：承诺突发尺寸，单位为byte。

· 如果不指定cbs参数，缺省取值为与62.5 × committed-information-rate的乘积最接近且不小于该乘积值的512的整数倍，但是最大值不能超过256000000。

· 如果指定cbs参数，取值范围512～256000000且必须为512的整数倍。

ebs excess-burst-size：超出突发尺寸，单位为byte。缺省值为512，单位为byte，取值范围为0～256000000且必须为512的整数倍。

pir peak-information-rate：峰值速率，不指定pps关键字时单位为kbps，指定pps关键字时单位为pps，pir和cir速率单位必须保持一致。peak-information-rate取值范围为8～160000000且必须为8的整数倍。

green action：数据包的流量符合承诺速率时对数据包采取的动作，缺省动作为pass。

red action：数据包的流量既不符合承诺速率也不符合峰值速率时对数据包采取的动作，缺省动作为discard。

yellow action：数据包的流量不符合承诺速率但是符合峰值速率时对数据包采取的动作，缺省动作为pass。

action：对数据包采取的动作，有以下几种：

· discard：丢弃数据包。

· pass：允许数据包通过。

· remark-dot1p-pass new-cos：设置新的802.1P报文的优先级值，并允许数据包通过，取值范围为0～7。

· remark-dscp-pass new-dscp：设置报文新的DSCP值，并允许数据包通过，取值范围为0～63。

· remark-lp-pass new-local-precedence：设置新的本地优先级，并允许数据包通过，取值范围为0～7。

【使用指导】

接口上应用的策略中使用car时，可以应用到接口报文的接收或者发送方向。

在同一个流行为中多次执行本命令，最后一次执行的命令生效。

如果未配置峰值速率，则表示所配置的是单速率流量监管，否则表示双速率流量监管。

【举例】

\# 为流行为配置流量监管。报文正常流速为200kbps，承诺突发尺寸为51200bytes，速率大于200kbps时，报文DSCP值改为0并发送。

<Sysname> system-view

[Sysname] traffic behavior database

[Sysname-behavior-database] car cir 200 cbs 51200 ebs 0 green pass red remark-dscp-pass 0


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-1825292436_6590520_812185388.htm -->

remark service-vlan-id命令用来重标记报文的SVLAN。

undo remark service-vlan-id命令用来恢复缺省情况。

【命令】

remark service-vlan-id vlan-id

undo remark service-vlan-id

【缺省情况】

未配置重新标记报文的SVLAN的动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

vlan-id：表示重标记报文外层VLAN（SVLAN）的编号，取值范围为1～4094。

【举例】

\# 在流行为b1上配置重标记报文的SVLAN为VLAN 222。

<Sysname> system-view

[Sysname] traffic behavior b1

[Sysname-behavior-b1] remark service-vlan-id 222


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-478332983_1426974163_-1769919105.htm -->

display qos car name命令用来显示聚合CAR的配置和统计信息。

【命令】

display qos car name [ car-name ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

car-name：聚合CAR的名称，首字符需要以字母开头，为1～31个字符的字符串，区分大小写。显示指定聚合CAR的配置和统计信息。如果未指定本参数，将显示所有聚合CAR的配置和统计信息。

【举例】

\# 显示聚合CAR的配置和统计信息。

<Sysname> display qos car name

 Name: a

 Mode: aggregative

 CIR 32 (kbps) CBS: 2048 (Bytes) PIR: 888 (kbps) EBS: 0 (Bytes)

 Green action: pass

 Yellow action: pass

 Red action: discard

 Slot 0:

 Green packets: 0 (Packets), 0 (Bytes)

 Yellow packets: 0 (Packets), 0 (Bytes)

 Red packets: 0 (Packets), 0 (Bytes)

 Slot 1:

 Green packets: 0 (Packets), 0 (Bytes)

 Yellow packets: 0 (Packets), 0 (Bytes)

 Red packets: 0 (Packets), 0 (Bytes)

 Slot 2:

 Apply failed

表6-1 display qos car name命令显示信息描述表

| Red packets | 红色报文的流量统计 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-478332983_1426974163_1167551116.htm -->

qos car命令用来配置聚合CAR。

undo qos car命令用来取消聚合CAR的配置。

【命令】

qos car car-name aggregative cir committed-information-rate [ cbs committed-burst-size [ ebs excess-burst-size ] ] [ green action | red action | yellow action ] *

qos car car-name aggregative cir committed-information-rate [ cbs committed-burst-size ] pir peak-information-rate [ ebs excess-burst-size ] [ green action | red action | yellow action ] *

undo qos car car-name

【缺省情况】

未配置聚合CAR。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

car-name：聚合CAR的名称，首字符需要以字母开头，为1～31个字符的字符串，区分大小写。

cir committed-information-rate：承诺信息速率，单位为kbps。取值范围为8～160000000且必须为8的整数倍。

cbs committed-burst-size：承诺突发尺寸，即实际平均速率在承诺速率以内时的突发流量，单位为byte。

· 如果不指定cbs参数，缺省取值为与62.5 × committed-information-rate的乘积最接近且不小于该乘积值的512的整数倍，但是最大值不能超过256000000。

· 如果指定cbs参数，取值范围512～256000000且必须为512的整数倍。

ebs excess-burst-size：过度突发尺寸，单位为byte。缺省值为512，取值范围为0～256000000且必须为512的整数倍。

pir peak-information-rate：峰值速率，单位为kbps。取值范围为8～160000000且必须为8的整数倍。

green action：数据包的流量符合承诺速率时对数据包采取的动作，缺省动作为pass。

red action：数据包的流量既不符合承诺速率也不符合峰值速率时对数据包采取的动作，缺省动作为discard。

yellow action：数据包的流量不符合承诺速率但是符合峰值速率时对数据包采取的动作，缺省动作为pass。

action：对数据包采取的动作，有以下几种：

· discard：丢弃数据包。

· pass：允许数据包通过。

· remark-dot1p-pass new-cos：设置新的802.1P报文的优先级值，并允许数据包通过，取值范围为0～7。

· remark-dscp-pass new-dscp：设置报文新的DSCP值，并允许数据包通过，取值范围为0～63；用文字表示时，可以选取af11、af12、af13、af21、af22、af23、af31、af32、af33、af41、af42、af43、cs1、cs2、cs3、cs4、cs5、cs6、cs7、default、ef。

【使用指导】

聚合CAR配置需要在接口上应用或在策略中引用后才能生效。

不配置峰值速率表示所配置的是单速率流量监管，否则表示双速率流量监管。

【举例】

\# 配置聚合CAR采取的CAR参数取值，cir取值为25600，cbs取值为512000，对于红色报文采取丢弃的动作。

<Sysname> system-view

[Sysname] qos car aggcar-1 aggregative cir 25600 cbs 512000 red discard

【相关命令】

· display qos car name


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-478332983_1426974163_1195430250.htm -->

car name命令用来配置聚合CAR动作。

undo car用来恢复缺省情况。

【命令】

car name car-name

undo car

【缺省情况】

未配置聚合CAR动作。

【视图】

流行为视图

【缺省用户角色】

network-admin

【参数】

car-name：聚合CAR的名称，首字符需要以字母开头，为1～31个字符的字符串，区分大小写。

【举例】

\# 配置流行为be1的聚合CAR动作为aggcar-1。

<Sysname> system-view

[Sysname] traffic behavior be1

[Sysname-behavior-be1] car name aggcar-1

【相关命令】

· display qos car name

· display traffic behavior user-defined


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-478332983_1426974163_645559111.htm -->

reset qos car name命令用来清除聚合CAR的统计信息。

【命令】

reset qos car name [ car-name ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

car-name：聚合CAR的名称，首字符需要以字母开头，为1～31个字符的字符串，区分大小写。清除指定聚合CAR的统计信息。如果未指定本参数，将清除所有聚合CAR的统计信息。

【举例】

\# 清除聚合CAR aggcar-1的统计信息。

<Sysname> reset qos car name aggcar-1


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-849934648_-1050563067_2134961744.htm -->

display qos gts interface命令用来显示接口的流量整形配置情况和统计信息。

【命令】

display qos gts interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的流量整形配置情况和统计信息。

【举例】

\# 显示所有接口的流量整形配置情况和统计信息。

<Sysname> display qos gts interface

Interface: Ten-GigabitEthernet1/0/1

 Rule: If-match acl 2001

 CIR 200 (kbps), CBS 51200 (Bytes), PIR 51200 (kbps), EBS 0 (Bytes)

 Queue Length: 100 (Packets)

 Queue Size: 70 (Packets)

 Passed: 0 (Packets) 0 (Bytes)

 Discarded: 0 (Packets) 0 (Bytes)

 Delayed: 0 (Packets) 0 (Bytes)

Interface: Ten-GigabitEthernet1/0/2

 Rule: If-match acl 2001

 CIR 64 (kbps), CBS 512 (Bytes), EBS 0 (Bytes)

 Queue Length: 100 (Packets)

 Queue Size: 70 (Packets)

 Passed: 0 (Packets) 0 (Bytes)

 Discarded: 0 (Packets) 0 (Bytes)

 Delayed: 0 (Packets) 0 (Bytes)

表3-1 display qos gts命令显示信息描述表

| Delayed | 被延迟发送的数据包数目和字节数 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-849934648_-1050563067_403118877.htm -->

qos gts命令用来在接口上配置流量整形。

undo qos gts命令用来取消接口上流量整形的配置。

【命令】

qos gts queue queue-id cir committed-information-rate [ cbs committed-burst-size ]

undo qos gts queue queue-id

【缺省情况】

接口上未配置流量整形。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

queue queue-id：对队列上的数据包进行流量整形。queue-id为匹配的队列号，取值范围为0～7。

cir committed-information-rate：承诺信息速率，单位为kbps。10GE端口的取值范围为8～10485760，40GE端口的取值范围为8～41943040，100GE端口的取值范围为8～104857600，用户配置的数值必须是8的倍数。

cbs committed-burst-size：承诺突发尺寸，单位为byte。

· 如果不指定cbs参数，缺省取值为与62.5 × committed-information-rate的乘积最接近且不小于该乘积值的512的整数倍，但是最大值不能超过16777216。

· 如果指定cbs参数，取值范围512～16777216且必须为512的整数倍。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上对队列1中的报文进行流量整形。正常流速为6400kbps，突发流量为51200bytes。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos gts queue 1 cir 6400 cbs 51200


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-849934648_-1739147666_-550880039.htm -->

display qos lr interface命令用来显示接口上的限速配置情况和统计信息。

【命令】

display qos lr interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的限速配置情况和运行统计信息。

【举例】

\# 显示所有接口的接口限速配置情况和统计信息。

<Sysname> display qos lr interface

Interface: Ten-GigabitEthernet1/0/1

 Direction: Inbound

 CIR 2000 (kbps), CBS 51200 (Bytes), EBS 0 (Bytes)

 Passed: 1000 (Packets) 1000 (Bytes)

 Discarded: 1000 (Packets) 1000 (Bytes)

 Delayed: 1000 (Packets) 1000 (Bytes)

Interface: Ten-GigabitEthernet1/0/2

 Direction: Outbound

 CIR 64 (kbps), CBS 512 (Bytes), EBS 0 (Bytes)

 Passed: 1000 (Packets) 1000 (Bytes)

 Discarded: 1000 (Packets) 1000 (Bytes)

 Delayed: 1000 (Packets) 1000 (Bytes)

表3-2 display qos lr命令显示信息描述表

| Delayed | 被延迟发送的数据包数目和字节数 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_-849934648_-1739147666_409608502.htm -->

qos lr命令用来配置限速。

undo qos lr命令用来取消配置的限速。

【命令】

qos lr { inbound | outbound } cir committed-information-rate [ cbs committed-burst-size ]

undo qos lr { inbound | outbound }

【缺省情况】

未配置限速。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

inbound：对接收的数据流进行限速。

outbound：对发送的数据流进行限速。

cir committed-information-rate：承诺信息速率，单位为kbps。10GE端口的取值范围为8～10485760，40GE端口的取值范围为8～41943040，100GE端口的取值范围为8～104857600，用户配置的数值必须是8的倍数。

cbs committed-burst-size：承诺突发尺寸，单位为bytes。

· 如果不指定cbs参数，缺省取值为与62.5 × committed-information-rate的乘积最接近且不小于该乘积值的512的整数倍，但是最大值不能超过134217728。

· 如果指定cbs参数，取值范围512～134217728且必须为512的整数倍。

【举例】

\# 对接口Ten-GigabitEthernet1/0/1上出方向的报文进行限速。正常流速为256kbps，突发流量为51200bytes，以后速率小于等于256kbps时正常发送，速率大于256kbps时，将进行限速。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos lr outbound cir 256 cbs 51200


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1061630023_264494165_-1896338072.htm -->

qos trust命令用来配置端口优先级信任模式。

undo qos trust命令用来恢复缺省情况。

【命令】

qos trust { dot1p | dscp }

undo qos trust

【缺省情况】

设备不信任报文携带的优先级，会使用端口优先级作为报文的802.1p优先级进行优先级映射。

【视图】

二层以太网接口/三层以太网接口

【缺省用户角色】

network-admin

【参数】

dot1p：信任报文自带的802.1p优先级，以此优先级进行优先级映射。

dscp：信任IP报文自带的DSCP，以此优先级进行优先级映射。

【使用指导】

如果希望设备信任AC入方向报文自带的优先级，则配置AC时指定的接口必须已经配置了优先级信任模式。配置AC的详细介绍请参见“VXLAN配置指导”。

VXLAN IP网关从AC接收到报文后，如果VXLAN IP网关对报文进行三层转发，则不管报文接收接口上是否配置qos trust dscp命令，设备都信任IP报文自带的DSCP优先级，以此优先级进行优先级映射；如果对报文进行二层转发，则只有在报文接收接口上配置了qos trust dscp命令，设备才会信任IP报文自带的DSCP优先级。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上配置优先级信任模式为信任报文自带的802.1p优先级。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos trust dot1p

【相关命令】

· display qos trust interface


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1061630023_264494165_168954480.htm -->

display qos trust interface命令用来显示端口优先级信任模式信息和端口优先级的信息。

【命令】

display qos trust interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定的接口类型和接口编号。如果未指定本参数，将显示所有接口的端口优先级信任模式信息。

【举例】

\# 显示端口优先级信任模式信息。

<Sysname> display qos trust interface ten-gigabitethernet 1/0/1

Interface: Ten-GigabitEthernet1/0/1

 Port priority trust information

 Port priority:4

 Port priority trust type: dscp

表2-3 display qos trust interface命令显示信息描述表

| Port priority trust type | 端口优先级信任类型，取值为： · dot1p：802.1p优先级 · dscp：DSCP优先级 · none：不信任任何优先级 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1061630023_389379986_-1871826451.htm -->

import命令用来配置指定优先级映射表的映射关系。

undo import命令用来删除配置的优先级映射表的映射关系，恢复其为缺省的映射关系。

【命令】

import import-value-list export export-value

undo import { import-value-list | all }

【缺省情况】

优先级映射表的映射关系请参见配置指导中的附录 B。

【视图】

优先级映射表视图

【缺省用户角色】

network-admin

【参数】

import-value-list：输入值列表。

export-value：输出值。

all：删除配置地该映射表的所有映射关系，恢复其为缺省的映射关系。

【举例】

\# 配置802.1p优先级到本地优先级映射表的映射关系，与802.1p优先级4、5相对应的本地优先级为1。

<Sysname> system-view

[Sysname] qos map-table dot1p-lp

[Sysname-maptbl-dot1p-lp] import 4 5 export 1

【相关命令】

· display qos map-table


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1061630023_389379986_1116151462.htm -->

display qos map-table命令用来显示优先级映射表配置情况。

【命令】

display qos map-table [ dot1p-dp | dot1p-exp | dot1p-lp | dscp-dot1p | dscp-dp | dscp-dscp | exp-dot1p ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

表2-1 优先级映射表

| exp-dot1p | EXP到802.1p优先级映射表 |
| --- | --- |

‌

【使用指导】

如果未指定表的类型，将显示所有映射表的配置情况。

【举例】

\# 显示802.1p优先级到本地优先级映射表的配置信息。

<Sysname> display qos map-table dot1p-lp

MAP-TABLE NAME: dot1p-lp TYPE: pre-define

IMPORT: EXPORT

 0: 2

 1: 0

 2: 1

 3: 3

 4: 4

 5: 5

 6: 6

 7: 7

表2-2 display qos map-table命令显示信息描述表

| EXPORT | 映射表的输出值 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1061630023_389379986_727216895.htm -->

qos map-table命令用来进入指定的优先级映射表视图。

【命令】

qos map-table { dot1p-dp | dot1p-exp | dot1p-lp | dscp-dot1p | dscp-dp | dscp-dscp | exp-dot1p }

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

其它参数请参见表2-1。

【举例】

\# 进入802.1p优先级到本地优先级映射表视图。

<Sysname> system-view

[Sysname] qos map-table dot1p-lp

[Sysname-maptbl-dot1p-lp]

【相关命令】

· display qos map-table

· import


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1061630023_959707258_1088682876.htm -->

qos priority命令用来配置端口的端口优先级。

undo qos priority命令用来恢复端口优先级为缺省值。

【命令】

qos priority [ dscp ] priority-value

undo qos priority [ dscp ]

【缺省情况】

端口优先级的缺省值为0，未配置修改报文的DSCP优先级的值。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

priority-value：端口优先级值。未配置DSCP关键字时，表示配置端口优先级，端口优先级的取值范围为0～7；配置DSCP关键字后，表示修改报文的DSCP优先级，取值范围为0～63。

【使用指导】

未配置端口优先级信任模式时，表示设备以端口优先级作为报文的802.1P优先级进行映射，如果携带dscp关键字，同时对于三层报文将改写报文的DSCP优先级。

配置端口优先级信任模式后，本命令将不再生效。

【举例】

\# 配置接口Ten-GigabitEthernet1/0/1的端口优先级为2。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos priority 2

【相关命令】

· display qos trust interface


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_-1387118818.htm -->

display qos wred interface命令用来显示WRED配置情况和统计信息。

【命令】

display qos wred interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定的接口类型和接口编号。如果未指定本参数，将显示所有接口的WRED配置情况和统计信息。

【举例】

\# 显示所有接口的WRED配置情况和统计信息。

<Sysname> display qos wred interface

Interface: Ten-GigabitEthernet1/0/3

 Current WRED configuration:

 Applied WRED table name: q1

表5-1 display qos wred interface命令显示信息描述表

| Applied WRED table name | 当前应用的WRED表的名称 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_-1764766577.htm -->

qos wred apply命令用来在接口上应用WRED表。

undo qos wred apply命令用来恢复缺省情况。

【命令】

qos wred apply [ table-name ]

undo qos wred apply

【缺省情况】

接口没有应用WRED表，即接口采用尾丢弃。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

table-name：WRED表的名称，为1～32个字符的字符串，区分大小写。如果未指定本参数，则在接口上应用缺省WRED表。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用WRED表。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wred apply table1

【相关命令】

· display qos wred interface

· display qos wred table

· qos wred queue table


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_-1840687235.htm -->

queue命令用来配置基于队列的WRED表的内容。

undo queue命令用来恢复缺省情况。

【命令】

queue queue-id [ drop-level drop-level ] low-limit low-limit high-limit high-limit [ discard-probability discard-prob ]

undo queue { queue-id | all }

【缺省情况】

WRED表在创建之后，有缺省的一套参数，low-limit的取值为100，high-limit的取值为1000，discard-prob的取值为10。

【视图】

WRED表视图

【缺省用户角色】

network-admin

【参数】

all：表示所有队列。

queue-id：队列编号。取值范围为0～7。

drop-level drop-level：丢弃级别，在进行报文丢弃时参考的参数，0对应绿色报文、1对应黄色报文、2对应红色报文。如果未指定本参数，后续配置的参数对该队列所有丢弃级别的报文都生效。

low-limit low-limit：队列平均长度的下限。取值范围为0～38000。

high-limit high-limit：队列平均长度的上限。取值范围为0～3800且必须大于丢弃下限。

discard-probability discard-prob：丢弃概率，取值越大，计算出的丢弃概率越小。取值范围为0～100。

【使用指导】

当队列平均长度小于下限时，不丢弃报文。当队列平均长度在上限和下限之间时，设备随机丢弃报文，队列越长，丢弃概率越高。当队列平均长度超过上限时，丢弃所有到来的报文。

【举例】

\# 配置基于队列的WRED表queue-table1中队列1的丢弃参数：丢弃级别为1，队列平均长度的下限为10，队列平均长度的上限为20，丢弃概率为30%。

<Sysname> system-view

[Sysname] qos wred queue table queue-table1

[Sysname-wred-table-queue-table1] queue 1 drop-level 1 low-limit 10 high-limit 20 discard-probability 30

【相关命令】

· display qos wred table

· qos wred queue table


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_1419256280.htm -->

queue ecn命令用来对指定队列开启拥塞通知功能。

undo queue ecn命令用来恢复缺省情况。

【命令】

queue queue-id ecn

undo queue queue-id ecn

【缺省情况】

对任何队列都未开启拥塞通知功能。

【视图】

WRED表视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列编号。取值范围为0～7。

【使用指导】

在报文的发送端和接收端都支持ECN功能时，设备可以通过对ECN域的识别和标记将拥塞状况告知终端，避免拥塞加剧。

【举例】

\# 在WRED表queue-table1中，对队列1开启拥塞通知功能。

<Sysname> system-view

[Sysname] qos wred queue table queue-table1

[Sysname-wred-table-queue-table1] queue 1 ecn

【相关命令】

· display qos wred table

· qos wred queue table


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_2115861592.htm -->

display qos wred table命令用来显示WRED表的配置情况。

【命令】

display qos wred table [ name table-name ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

name table-name：WRED表的名称，为1～32个字符的字符串，区分大小写。如果未指定本参数，则显示所有WRED表配置情况。

slot slot-number：显示指定成员设备的WRED表配置情况。slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主用设备的WRED表配置情况。

【举例】

\# 显示WRED表1的配置情况，表1是一个已经配置好的WRED参数表。

<Sysname> display qos wred table name 1

Table name: 1

Table type: Queue based WRED

QID gmin gmax gprob ymin ymax yprob rmin rmax rprob exponent ECN

----------------------------------------------------------------------------

0 100 1000 10 100 1000 10 100 1000 10 9 N

1 100 1000 10 100 1000 10 100 1000 10 9 N

2 100 1000 10 100 1000 10 100 1000 10 9 N

3 100 1000 10 100 1000 10 100 1000 10 9 N

4 100 1000 10 100 1000 10 100 1000 10 9 N

5 100 1000 10 100 1000 10 100 1000 10 9 N

6 100 1000 10 100 1000 10 100 1000 10 9 N

7 100 1000 10 100 1000 10 100 1000 10 9 N

表5-2 display qos wred table命令显示信息描述表

| ECN | 是否对该队列开启了拥塞通知功能，Y表示开启，N表示未开启 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_405835983.htm -->

qos wred queue table命令用来创建WRED表，同时进入该WRED表视图。如果指定的WRED表已经存在，则直接进入WRED表视图。

undo qos wred queue table命令用来删除WRED表。

【命令】

qos wred queue table table-name

undo qos wred queue table table-name

【缺省情况】

设备上不存在WRED表。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

table table-name：指定WRED表的名称，为1～32个字符的字符串，区分大小写。

【使用指导】

设备不允许删除正在使用的WRED表。如果需要删除正在使用的表，请先在接口上取消应用的WRED表。

缺省WRED表可以通过display qos wred table命令显示，不允许修改和删除。

【举例】

\# 创建基于queue的WRED表queue-table1。

<Sysname> system-view

[Sysname] qos wred queue table queue-table1

[Sysname-wred-table-queue-table1]

【相关命令】

· display qos wred table


---

<!-- 08-ACL和QoS命令参考/html/-756741229_1524994952_-289698017_778291140.htm -->

queue weighting-constant命令用来配置计算平均队列长度的指数。

undo queue weighting-constant命令用来恢复缺省情况。

【命令】

queue queue-id weighting-constant exponent

undo queue queue-id weighting-constant

【缺省情况】

计算平均队列长度的指数为9。

【视图】

WRED表视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列编号。取值范围为0～7。

weighting-constant exponent：计算平均队列长度的指数。取值范围为0～15。

【使用指导】

平均队列长度的指数越大，计算平均队列长度时对队列的实时变化越不敏感。计算队列平均长度的公式为：平均队列长度=（以前的平均队列长度×（1-1/2n））＋（当前队列长度×（1/2n））。其中n表示指数。

【举例】

\# 在WRED表queue-table1中，配置计算平均队列长度的指数为12。

<Sysname> system-view

[Sysname] qos wred queue table queue-table1

[Sysname-wred-table-queue-table1] queue 1 weighting-constant 12

【相关命令】

· display qos wred table

· qos wred queue table


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1053827835_-1087719788.htm -->

qos wfq group sp命令用来配置队列加入SP组，采用严格优先级调度算法。

undo qos wfq group sp命令用来取消将队列加入SP组。

【命令】

qos wfq queue-id group sp

undo qos wfq queue-id

【缺省情况】

当接口使用WFQ队列时，所有队列均处于WFQ调度组1中。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或表4-4中的关键字。

【使用指导】

本命令需要在端口队列为WFQ调度模式下使用。

SP组与普通WFQ优先组不同，加入SP组的端口队列采用严格优先级调度算法，不再采用加权轮循调度算法。调度时先调度SP组，然后调度其他WFQ优先组。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用WFQ队列，并配置队列0加入SP组进行严格优先级调度。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq weight

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq 0 group sp

【相关命令】

· display qos queue wfq interface

· qos bandwidth queue

· qos wfq


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1053827835_-1598932649.htm -->

qos bandwidth queue命令用来配置端口队列的最小带宽保证。

undo qos bandwidth queue命令用来恢复缺省情况。

【命令】

qos bandwidth queue queue-id min bandwidth-value

undo qos bandwidth queue queue-id

【缺省情况】

在使用WFQ队列时，每个队列的最小带宽保证为0kbps。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或表4-4中的关键字。

min bandwidth-value：最小保证带宽值，单位为kbps。端口流量拥塞时能够保证的最小队列带宽。10GE端口的取值范围为8～10000000，40GE端口取值范围为8～40000000，100GE端口的取值范围为8～100000000，表示端口流量拥塞时能够保证的最小队列带宽。

【使用指导】

必须先使用qos wfq命令在接口上开启WFQ队列，然后才能进行本配置。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上配置队列0的最小保证带宽值为100kbps。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq weight

[Sysname-Ten-GigabitEthernet1/0/1] qos bandwidth queue 0 min 100

【相关命令】

· qos wfq


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1053827835_-1677267433.htm -->

qos wfq { byte-count | weight }命令用来配置WFQ队列或修改WFQ队列的参数。

undo qos wfq命令用来取消WFQ队列调度参数的配置。

【命令】

qos wfq queue-id group 1 { byte-count | weight } schedule-value

undo qos wfq queue-id

【缺省情况】

当接口使用WFQ队列时，所有队列都处于WFQ调度组1中，各队列的调度权重均为1。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或表4-4中的关键字。

group 1：表示该队列属于WFQ优先组，目前仅支持1个WRR调度组。

byte-count：表示按照每次轮询可发送的字节数进行计算。

weight：表示按照每次轮询可发送的报文个数进行计算。

schedule-value：配置队列的调度权重，取值范围为1～15。

【使用指导】

必须先使用qos wfq命令在接口上开启WFQ队列，然后才能进行本配置。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用WFQ队列，并按照每次轮询可发送的字节数进行计算，配置队列0的调度权重为10。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq byte-count

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq 0 group 1 byte-count 10

【相关命令】

· display qos queue wfq interface

· qos bandwidth queue

· qos wfq


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1053827835_-420956602.htm -->

display qos queue wfq interface命令用来显示接口的WFQ配置情况。

【命令】

display qos queue wfq interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的WFQ配置情况。

【举例】

\# 显示接口Ten-GigabitEthernet1/0/1的加权公平队列配置情况。

<Sysname> display qos queue wfq interface ten-gigabitethernet 1/0/1

Interface: Ten-GigabitEthernet1/0/1

 Output queue: Hardware Weighted Fair Queuing

 Queue ID Queue name Group Byte count Min Bandwidth

 --------------------------------------------------------------------------------

 0 be 1 1 0

 1 af1 1 1 0

 2 af2 1 1 0

 3 af3 1 1 0

 4 af4 1 1 0

 5 ef 1 1 0

 6 cs6 1 1 0

 7 cs7 1 1 0

表4-5 display qos queue wfq interface命令显示信息描述表

| Min-Bandwidth | 队列的最小保证带宽值 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1053827835_104507154.htm -->

qos wfq命令用来在接口上开启WFQ队列。

undo qos wfq命令用来恢复缺省情况。

【命令】

qos wfq { byte-count | weight }

undo qos wfq { byte-count | weight }

【缺省情况】

接口采用WRR调度算法，各队列按照每次轮询可发送的字节数进行计算。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

byte-count：表示按照每次轮询可发送的字节数进行计算。

weight：表示按照每次轮询可发送的报文个数进行计算。

【使用指导】

必须先使用qos wfq命令在接口上开启WFQ队列，然后才能进行WFQ配置。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上开启WFQ队列，并按照每次轮询可发送的报文个数进行计算。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq weight

\# 在接口Ten-GigabitEthernet1/0/1上开启WFQ队列，并按照每次轮询可发送的字节数进行计算。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wfq byte-count

【相关命令】

· display qos queue wfq interface


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1572391472_-116061572.htm -->

display qos queue-statistics interface outbound命令用来显示端口队列出方向的统计信息。

【命令】

display qos queue-statistics interface [ interface-type interface-number ] outbound

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的队列出方向统计信息。

【举例】

\# 显示接口Ten-GigabitEthernet1/0/1的队列出方向统计信息。

<Sysname> display qos queue-statistics interface ten-gigabitethernet 1/0/1 outbound

Interface: Ten-GigabitEthernet1/0/1

 Direction: outbound

 Forwarded: 0 packets, 0 bytes

 Dropped: 0 packets, 0 bytes

 Queue 0

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 1

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 2

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 3

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 4

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 5

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 6

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

 Queue 7

 Forwarded: 0 packets, 0 bytes, 0 pps, 0 bps

 Dropped: 0 packets, 0 bytes

 Current queue length: 0 packets

表4-6 display qos queue-statistics interface outbound命令显示信息描述表

| Current queue length | 当前队列长度 |
| --- | --- |

【相关命令】

reset counters interface（接口管理命令参考/以太网接口）


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1859310296_-1672874935.htm -->

bandwidth queue命令用来配置队列调度策略下队列的最小带宽保证。

undo bandwidth queue命令用来恢复缺省情况。

【命令】

bandwidth queue queue-id min bandwidth-value

undo bandwidth queue queue-id

【缺省情况】

在队列调度策略中配置某个队列为WFQ队列后，该队列的最小带宽保证为0kbps。

【视图】

队列调度策略视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或表4-4中的关键字。

min bandwidth-value：最小保证带宽值，单位为kbps。端口流量拥塞时能够保证的最小队列带宽。取值范围为8～100000000，单位为kbps，表示端口流量拥塞时能够为该队列保证的最小带宽。

【使用指导】

必须先在队列调度策略中将某个队列配置为WFQ队列，才能为该队列配置最小带宽保证。

【举例】

\# 在队列调度策略myprofile中，配置队列0使用WFQ队列算法，使用报文个数作为调度权重，权重值为1，分组为1，并为该队列配置最小保证带宽值为100kbps。

<Sysname> system-view

[Sysname] qos qmprofile myprofile

[Sysname-qmprofile-myprofile] queue 0 wfq group 1 weight 1

[Sysname-qmprofile-myprofile] bandwidth queue 0 min 100


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1859310296_-590681846.htm -->

qos qmprofile命令用来创建用户自定义的队列调度策略，并进入相应的队列调度策略视图。如果指定的队列调度策略已经存在，则直接进入该队列调度策略视图。

undo qos qmprofile命令用来删除用户自定义的队列调度策略。

【命令】

qos qmprofile profile-name

undo qos qmprofile profile-name

【缺省情况】

不存在用户自定义的队列调度策略。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

profile-name：队列调度策略名称，为1～31个字符的字符串，区分大小写。

【使用指导】

如果需要删除已经应用到接口的队列调度策略，必须先在应用的位置上取消对该队列调度策略的应用，然后再删除该队列调度策略。

【举例】

\# 创建队列调度策略myprofile，并进入队列调度策略视图。

<Sysname> system-view

[Sysname] qos qmprofile myprofile

[Sysname-qmprofile-myprofile]

【相关命令】

· display qos qmprofile interface

· queue


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1859310296_-77942537.htm -->

display qos qmprofile interface命令用来显示接口的队列调度策略的配置情况。

【命令】

display qos qmprofile interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的队列调度策略的配置情况。

【举例】

\# 显示指定接口的队列调度策略的配置情况。

<Sysname> display qos qmprofile interface ten-gigabitethernet 1/0/1

Interface: Ten-GigabitEthernet1/0/1

 Queue management profile: myprofile

表4-8 display qos qmprofile interface命令显示信息描述表

| Queue management profile | 队列调度策略名称 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1859310296_1355636764.htm -->

queue命令用来配置队列调度参数。

undo queue命令用来取消队列调度参数的配置。

【命令】

queue queue-id { sp | wfq group group-id { weight | byte-count } schedule-value | wrr group group-id { weight | byte-count } schedule-value }

undo queue queue-id

【缺省情况】

队列调度策略的内容是所有队列均采用WRR方式调度。

【视图】

队列调度策略视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或表4-4中的关键字。

sp：配置队列为严格优先级调度。

wfq：配置队列为加权公平调度。

wrr：配置队列为加权轮询调度。

group group-id：优先组号。取值只能为1。

byte-count：表示按照每次轮询可发送的字节数进行计算。

weight：表示按照每次轮询可发送的报文个数进行计算。

schedule-value：配置队列的调度权重。取值范围为1～15。

【举例】

\# 创建自定义的队列调度策略myprofile，并配置队列0为严格优先级调度。

<Sysname> system-view

[Sysname] qos qmprofile myprofile

[Sysname-qmprofile-myprofile] queue 0 sp

\# 创建自定义的队列调度策略myprofile，并配置队列1为加权轮询调度，权重为10，分组为1。

<Sysname> system-view

[Sysname] qos qmprofile myprofile

[Sysname-qmprofile-myprofile] queue 1 wrr group 1 weight 10

【相关命令】

· display qos qmprofile interface

· qos qmprofile


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1859310296_1679928729.htm -->

qos apply qmprofile命令用来在接口上应用队列调度策略。

undo qos apply qmprofile命令用来恢复缺省情况。

【命令】

qos apply qmprofile profile-name

undo qos apply qmprofile

【缺省情况】

接口上未应用队列调度策略。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

profile-name：队列调度策略名称，为1～31个字符的字符串，区分大小写。

【使用指导】

每个接口只能应用一个队列调度策略。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用队列调度策略myprofile。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos apply qmprofile myprofile

【相关命令】

· display qos qmprofile interface


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1859310296_2031902826.htm -->

display qos qmprofile configuration命令用来显示队列调度策略的配置情况。

【命令】

display qos qmprofile configuration [ profile-name ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

profile-name：队列调度策略名称，为1～31个字符的字符串，区分大小写。如果未指定本参数，则显示所有队列调度策略的配置情况。

slot slot-number：显示指定成员设备的队列调度策略的配置情况。slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主用设备的队列调度策略的配置情况。

【举例】

\# 显示队列调度策略myprofile的配置情况。

<Sysname> display qos qmprofile configuration myprofile

Queue management profile: myprofile (ID 1)

 Queue ID Type Group Schedule Schedule Min Max

 unit value bandwidth bandwidth

 ---------------------------------------------------------------------

 be WRR 1 weight 1 N/A N/A

 af1 WRR 1 weight 2 N/A N/A

 af2 WRR 1 weight 3 N/A N/A

 af3 WRR 1 weight 4 N/A N/A

 af4 WRR 1 weight 5 N/A N/A

 ef WRR 1 weight 9 N/A N/A

 cs6 WRR 1 weight 13 N/A N/A

 cs7 WRR 1 weight 15 N/A N/A

表4-7 display qos qmprofile configuration命令显示信息描述表

| Max bandwidth | 最大带宽值，N/A表示无效 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1894142876_1357505212.htm -->

display qos queue sp interface命令用来显示接口的SP（Strict Priority，严格优先级）队列配置情况。

【命令】

display qos queue sp interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的SP队列配置情况。

【举例】

\# 显示Ten-GigabitEthernet1/0/1的严格优先级队列配置情况。

<Sysname> display qos queue sp interface ten-gigabitethernet 1/0/1

Interface: Ten-GigabitEthernet1/0/1

 Output queue: Strict Priority queuing

表4-2 display qos queue sp interface命令显示信息描述表

| Output queue | 当前出队列类型 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_-1894142876_1601148081.htm -->

qos sp命令用来在接口上配置严格优先队列。

undo qos sp命令用来恢复缺省情况。

【命令】

qos sp

undo qos sp

【缺省情况】

接口采用WRR调度算法，各队列按照每次轮询可发送的字节数进行计算。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用SP模式的队列调度。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos sp

【相关命令】

· display qos queue sp interface


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_1802461367_1221317809.htm -->

display qos queue interface命令用来显示接口上队列配置情况和统计信息。

【命令】

display qos queue interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的接口队列配置情况和运行统计信息。

【举例】

\# 显示所有接口下的队列信息。

<Sysname> display qos queue interface

Interface: Ten-GigabitEthernet1/0/1

 Output queue: Weighted Round Robin queuing

 Queue ID Queue name Group Byte count

 ---------------------------------------------------

 0 be 1 1

 1 af1 1 2

 2 af2 1 3

 3 af3 1 4

 4 af4 1 5

 5 ef 1 9

 6 cs6 1 13

 7 cs7 1 15

Interface: Ten-GigabitEthernet1/0/2

 Output queue: Weighted Round Robin queuing

 Queue ID Queue name Group Byte count

 ---------------------------------------------------

 0 be 1 1

 1 af1 1 2

 2 af2 1 3

 3 af3 1 4

 4 af4 1 5

 5 ef 1 9

 6 cs6 1 13

 7 cs7 1 15

表4-1 display qos queue interface命令显示信息描述表

| Weight | 各个队列的调度权重，当前WRR队列调度权重的计算方式为按照每次轮询可发送的报文个数进行计算，N/A表示该队列采用SP调度算法 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_1850019327_-142176047.htm -->

display qos queue wrr interface命令用来显示接口的WRR（Weighted Round Robin，加权轮询）队列配置情况。

【命令】

display qos queue wrr interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有接口的WRR队列配置情况。

【举例】

\# 显示接口Ten-GigabitEthernet1/0/1的WRR队列配置情况。

<Sysname> display qos queue wrr interface ten-gigabitethernet 1/0/1

Interface: Ten-GigabitEthernet1/0/1

 Output queue: Weighted Round Robin queuing

 Queue ID Queue name Group Byte count

 --------------------------------------------------------

 0 be 1 1

 1 af1 1 1

 2 af2 1 1

 3 af3 1 1

 4 af4 1 1

 5 ef 1 1

 6 cs6 1 1

 7 cs7 sp N/A

表4-3 display qos queue wrr interface命令显示信息描述表

| Byte count | 各个队列的调度权重，当前WRR队列调度权重的计算方式为按照每次轮询可发送的字节数进行计算 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_1850019327_1331926813.htm -->

qos wrr group sp命令用来配置队列加入SP组，采用严格优先级调度算法。

undo qos wrr group sp命令用来取消将队列加入SP组。

【命令】

qos wrr queue-id group sp

undo qos wrr queue-id

【缺省情况】

当接口使用WRR队列时，所有队列均处于WRR调度组1中。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或表4-4中的关键字。

【使用指导】

本命令需要在端口队列为WRR调度模式下使用。

SP组与普通WRR优先组不同，加入SP组的端口队列采用严格优先级调度算法，不再采用加权轮循调度算法。调度时先调度SP组，然后调度其他WRR优先组。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用WRR队列，并配置队列0加入SP组进行严格优先级调度。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wrr weight

[Sysname-Ten-GigabitEthernet1/0/1] qos wrr 0 group sp

【相关命令】

· display qos queue wrr interface

· qos wrr


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_1850019327_32901168.htm -->

qos wrr { byte-count | weight }命令用来配置WRR队列或修改WRR队列的参数。

undo qos wrr命令用来取消WRR队列调度参数的配置。

【命令】

qos wrr queue-id group 1 { byte-count | weight } schedule-value

undo qos wrr queue-id

【缺省情况】

所有队列都处于WRR调度组1中，调度权重从队列0到7分别为1、2、3、4、5、9、13、15，各队列按照每次轮询可发送的字节数进行计算。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

queue-id：队列序号。取值范围为0～7或[表4-4](#_Ref453675913)中的关键字。

表4-4 queue-id数字和关键字对应表

| 7 | cs7 |
| --- | --- |

group 1：表示该队列属于WRR优先组，目前仅支持1个WRR调度组。

byte-count：表示按照每次轮询可发送的字节数进行计算。

weight：表示按照每次轮询可发送的报文个数进行计算。

schedule-value：配置队列的调度权重，取值范围为1～15。

【使用指导】

必须先使用qos wrr命令在接口上开启WRR队列，然后才能进行本配置。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上应用WRR队列，并按照每次轮询可发送的字节数进行计算，配置队列0的调度权重为10。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wrr byte-count

[Sysname-Ten-GigabitEthernet1/0/1] qos wrr 0 group 1 byte-count 10

【相关命令】

· display qos queue wrr interface

· qos wrr


---

<!-- 08-ACL和QoS命令参考/html/-756741229_660201308_1850019327_912170314.htm -->

qos wrr命令用来在接口上开启WRR队列。

undo qos wrr命令用来恢复缺省情况。

【命令】

qos wrr { byte-count | weight }

undo qos wrr { byte-count | weight }

【缺省情况】

接口采用WRR调度算法，各队列按照每次轮询可发送的字节数进行计算。

【视图】

二层以太网接口视图/三层以太网接口视图

【缺省用户角色】

network-admin

【参数】

byte-count：表示按照每次轮询可发送的字节数进行计算。

weight：表示按照每次轮询可发送的报文个数进行计算。

【使用指导】

必须先使用qos wrr命令在接口上开启WRR队列，然后才能进行WRR配置。

【举例】

\# 在接口Ten-GigabitEthernet1/0/1上开启WRR队列，并按照每次轮询可发送的报文个数进行计算。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wrr weight

\# 在接口Ten-GigabitEthernet1/0/1上开启WRR队列，并按照每次轮询可发送的字节数进行计算。

<Sysname> system-view

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qos wrr byte-count

【相关命令】

· display qos queue wrr interface


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_-1027737042.htm -->

qcn priority命令用来配置CNPV，加入CND。

undo qcn priority命令用来退出CND，同时删除此CND下的所有配置。

【命令】

qcn priority priority { admin [ defense-mode { disabled | edge | interior | interior-ready } alternate alternate-value ] | auto }

undo qcn priority priority

【缺省情况】

设备未加入任何CND。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

priority：CNPV优先级，取值范围为0～7。此CNPV优先级不能和全局或者接口下的admin模式下的隔离优先级冲突。

admin：配置方式。

defense-mode：接口保护模式，缺省为interior模式。

disabled：接口的优先级映射按优先级映射表起作用，不受QCN配置影响。

edge：CNPV优先级的报文需要被改写成隔离优先级。

interior：优先级保持不变，不按优先级映射表映射。出方向时删掉CN tag。

interior-ready：优先级保持不变，不按优先级映射表映射。出方向时保留CN tag。

alternate alternate-value：隔离优先级，取值范围为0～7，缺省为0。此隔离优先级不能和已有CNPV域冲突。

auto：LLDP协商方式。

【使用指导】

配置auto方式后，接口保护模式由LLDP协商得到，隔离优先级为小于CNPV且最接近CNPV的优先级值，如果小于CNPV的优先级值都被域占用，隔离优先级为大于CNPV且最接近CNPV的未被占用的优先级值。

【举例】

\# 配置设备加入CND，CNPV为2，模式选择方式为LLDP协商方式。

<Sysname> system-view

[Sysname] qcn priority 2 auto

\# 配置设备加入CND，CNPV为1，模式选择方式为配置方式，保护模式为disabled，隔离优先级为0。

<Sysname> system-view

[Sysname] qcn priority 1 admin defense-mode disabled alternate 0

【相关命令】

· qcn port priority


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_-1133530325.htm -->

display qcn profile命令用来显示QCN的profile运行信息。

【命令】

display qcn profile [ profile-id | default ] [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

profile-id：显示指定profile的运行信息。profile-id的取值范围为1～128。

default：显示缺省profile（即ID为0的profile）的运行信息。

slot slot-number：显示指定成员设备上QCN的profile运行信息。slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主用设备上QCN的profile运行信息。

【使用指导】

如果未指定profile-id和default参数，将显示所有profile的运行信息。

【举例】

\# 显示QCN的profile运行信息。

<Sysname> display qcn profile

Slot 1:

 Profile Set-point Weight

---------------------------------------------------

 default 26000 1

 1 30000 2

表1-4 display qcn profile命令显示信息描述表

| Weight | 权重 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_-2102392031.htm -->

qcn profile命令用来创建profile。

undo qcn profile命令用来删除profile。

【命令】

qcn profile profile-id set-point length-value weight weight-value

undo qcn profile profile-id

【缺省情况】

不存在profile。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

profile-id：指定的profile ID。系统自动创建缺省profile，ID为0，参数不能修改。profile-id的取值范围为1～128。

set-point length-value：期望队列长度，单位为byte。length-value的取值范围为16644～8320000。

weight weight-value：权重参数。weight-value的取值范围为-2～5。

【举例】

\# 创建profile，ID为1，期望队列长度为28000bytes，权重为1。

<Sysname> system-view

[Sysname] qcn profile 1 set-point 28000 weight 1


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_-566752835.htm -->

reset qcn cp interface命令用来清除CP端的统计信息。

【命令】

reset qcn cp interface [ interface-type interface-number ] [ priority priority ]

【视图】

用户视图

【缺省用户角色】

network-admin

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将清除所有二层以太网接口下的统计信息。

priority priority：CNPV优先级，取值范围为0～7。如果未指定本参数，将清除对应接口加入的所有CNPV域统计信息。

【举例】

\# 清除所有域所有二层以太网接口CP端的统计信息。

<Sysname> reset qcn cp interface

【相关命令】

· display qcn cp interface


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_-90085658.htm -->

qcn enable命令用来开启QCN功能。

undo qcn enable命令用来关闭QCN功能。

【命令】

qcn enable

undo qcn enable

【缺省情况】

QCN功能处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

开启QCN功能后，其它QCN配置才能生效。

【举例】

\# 开启QCN功能。

<Sysname> system-view

[Sysname] qcn enable


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_-971824278.htm -->

display qcn interface命令用来显示QCN的接口运行信息。

【命令】

display qcn interface [ interface-type interface-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有二层以太网接口的运行信息。

【举例】

\# 显示QCN的接口运行信息。

<Sysname> display qcn interface

Interface: XGE1/0/1

 CNPV Mode Defense-mode Alternate

---------------------------------------------------

 1 comp interior-ready 4

 2 admin edge 0

 3 auto edge 0

Interface: XGE1/0/2

 CNPV Mode Defense-mode Alternate

---------------------------------------------------

 1 comp interior-ready 4

 2 admin edge 0

 3 auto edge 0

表1-3 display qcn interface命令显示信息描述表

| Alternate | 隔离优先级 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_1030307939.htm -->

qcn priority profile命令用来为CND绑定profile。

undo qcn priority profile命令用来取消为指定CND绑定profile的配置。

【命令】

qcn priority priority profile profile-id

undo qcn priority priority profile

【缺省情况】

CND绑定缺省profile。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

priority：CNPV优先级，取值范围为0～7。

profile-id：指定的profile ID。此处不包括缺省profile ID。

【使用指导】

如果设备还没有加入对应CND或指定的profile不存在，则不能绑定profile。

【举例】

\# 为CNPV值为2的CND绑定profile 2。

<Sysname> system-view

[Sysname] qcn priority 2 profile 2


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_1269894548.htm -->

display qcn cp interface命令用来显示CP端的统计信息。

【命令】

display qcn cp interface [ interface-type interface-number ] [ priority priority ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

interface-type interface-number：指定接口类型和接口编号。如果未指定本参数，将显示所有二层以太网接口下的统计信息。

priority priority：CNPV优先级，取值范围为0～7。如果未指定本参数，将显示设备加入的所有CND的统计信息。

【举例】

\# 显示所有二层以太网接口下的统计信息。

<Sysname> display qcn cp interface

Interface: XGE1/0/1

 CNPV 1: CP profile 1

 Passed: 100000 (Packets)

 Discarded: 10 (Packets)

 CNM count: 3000 (Packets)

CNPV 2: CP profile default

 Passed: 200000 (Packets)

 Discarded: 20 (Packets)

 CNM count: 3000 (Packets)

Interface: XGE1/0/2

 CNPV 1: CP profile 1

 Passed: 100000 (Packets)

 Discarded: 10 (Packets)

 CNM count: 3000 (Packets)

 CNPV 2: CP profile default

 Passed: 200000 (Packets)

 Discarded: 20 (Packets)

 CNM count: 3000 (Packets)

表1-1 display qcn cp interface命令显示信息描述表

| CNM count | 发送的CNM报文数 |
| --- | --- |

【相关命令】

· reset qcn cp interface


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_189263281.htm -->

qcn port priority命令用来配置优先级的保护模式选择方式。

undo qcn port priority命令用来取消指定优先级的保护模式选择方式的配置。

【命令】

qcn port priority priority { admin [ defense-mode { disabled | edge | interior | interior-ready } alternate alternate-value ] | auto }

undo qcn port priority priority

【缺省情况】

以全局配置为准。

【视图】

二层以太网接口视图

【缺省用户角色】

network-admin

【参数】

priority：CNPV优先级，取值范围为0～7。

admin：配置方式。

defense-mode：接口保护模式，缺省为disabled模式。

disabled：接口的优先级映射按优先级映射表起作用，不受QCN配置影响。

edge：CNPV优先级的报文需要被改写成隔离优先级。

interior：优先级保持不变，不按优先级映射表映射。出方向时删掉CN tag。

interior-ready：优先级保持不变，不按优先级映射表映射。出方向时保留CN tag。

alternate alternate-value：隔离优先级，取值范围为0～7，缺省为0。此隔离优先级不能和已有CNPV域冲突。

auto：LLDP协商方式。

【使用指导】

如果设备还没有加入对应CND，不能在接口下配置保护模式选择方式。

对于接口而言，接口下的配置优于全局配置生效。

【举例】

\# 配置在CNPV为1的CND中接口Ten-GigabitEthernet1/0/1的保护模式为disabled，隔离优先级为0。

<Sysname> system-view

[Sysname] qcn priority 1 auto

[Sysname] interface ten-gigabitethernet 1/0/1

[Sysname-Ten-GigabitEthernet1/0/1] qcn port priority 1 admin defense-mode disabled alternate 0

\# 配置接口Ten-GigabitEthernet1/0/2的模式选择方式为LLDP协商方式。

<Sysname> system-view

[Sysname] qcn priority 2 admin

[Sysname] interface ten-gigabitethernet 1/0/2

[Sysname-Ten-GigabitEthernet1/0/2] qcn port priority 2 auto

【相关命令】

· qcn priority


---

<!-- 08-ACL和QoS命令参考/html/-764605505_1125565456_835507657_1959911427.htm -->

display qcn global命令用来显示QCN的全局运行信息。

【命令】

display qcn global [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

slot slot-number：显示指定成员设备上QCN的全局运行信息。slot-number表示设备在IRF中的成员编号。如果未指定本参数，则显示主用设备上QCN的全局运行信息。

【举例】

\# 显示QCN的全局运行信息。

<Sysname> display qcn global

Slot 1:

QCN global status: Enabled

 CNPV Mode Defense-mode Alternate CP-profile

---------------------------------------------------

 1 admin interior-ready 4 default

 2 auto - 0 1

 3 auto - 0 1

表1-2 display qcn global命令显示信息描述表

| CP-profile | CP profile ID |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/00-前言.htm -->

前 言

本命令参考主要介绍S6800系列以太网交换机配置ACL和QoS功能时涉及的各种命令，包括创建ACL、配置QoS策略，以及配置流量监管、流量整形、拥塞管理等常用QoS技术时所使用的命令。

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


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664.htm -->

## 1.1 数据缓冲区配置命令

数据缓冲区的配置比较复杂，而且对设备的转发功能有重要的影响，建议用户不要轻易修改数据缓冲区的参数。在需要较大的缓存空间时，建议使用Burst功能来自动分配缓冲区。

burst-mode enable与buffer apply命令互斥，用户在开启Burst功能后，不能应用手工配置数据缓冲区的相应配置，反之亦然。如果已经使用某一种方式进行了配置，则必须先取消该方式的配置之后，才能使用另外一种方式进行配置。


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_-1115359753.htm -->

burst-mode enable命令用来开启Burst功能。

undo burst-mode enable命令用来关闭Burst功能。

【命令】

burst-mode enable

undo burst-mode enable

【缺省情况】

Burst功能处于关闭状态。

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

在下列情况下，Burst功能可以提供更好的报文缓存功能和流量转发性能：

· 广播或者组播报文流量密集，瞬间突发大流量的网络环境中；

· 报文从高速链路进入设备，由低速链路转发出去；或者报文从相同速率的多个接口同时进入设备，由一个相同速率的接口转发出去。

用户可以通过开启Burst功能，降低设备在上述特定环境中的报文丢包率，提高对报文的处理能力。

【举例】

\# 开启Burst功能。

<Sysname> system-view

[Sysname] burst-mode enable


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_-1443673174.htm -->

buffer apply命令用来应用用户对数据缓冲区所做的配置。

undo buffer apply命令用来恢复缺省情况。

【命令】

buffer apply

undo buffer apply

【视图】

系统视图

【缺省用户角色】

network-admin

【使用指导】

用户对数据缓冲区进行配置后，必须使用buffer apply命令进行应用，这些配置才能生效。

配置被应用后就不能被修改，需要先取消应用，再修改、应用，新的配置才能生效。

【举例】

\# 应用用户对数据缓冲区所做的配置。

<Sysname> system-view

[Sysname] buffer apply


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_-579977976.htm -->

buffer queue shared命令用来配置队列最多可使用的共享区域的比例。

undo buffer queue shared命令用来取消指定队列最多可使用的共享区域的比例的配置。

【命令】

buffer egress [ slot slot-number ] cell queue queue-id shared ratio ratio

undo buffer egress [ slot slot-number ] cell queue queue-id shared

【缺省情况】

所有队列最多可使用的共享区域比例均为33%。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

egress：表示对发送数据缓冲区进行配置。

slot slot-number：表示设备在IRF中的成员编号。不指定该参数时，表示配置所有成员设备。

cell：配置队列在cell资源中的最大共享缓存区的比例。

queue-id：需要配置的队列编号，取值范围为0～7。

ratio ratio：队列的最大共享缓存占用比，以百分数形式表示。该参数的取值范围为0～100。

【使用指导】

缺省情况下，所有队列均分共享区域，但用户也可以调整指定队列最多可使用的共享区域的比例，其它未配置的队列最多可使用的共享区域的比例仍遵循缺省值。最终，各队列最多可使用的共享区域的大小将由芯片根据buffer shared配置，以及实际需要收发报文的数量决定。

数据缓冲区的配置比较复杂，而且对设备的转发功能有重要的影响，建议用户不要轻易修改数据缓冲区的参数。在需要较大的缓存空间时，建议使用Burst功能来自动分配缓冲区。

【举例】

\# 配置队列0在cell资源中的最大共享缓存占用比为10%。

<Sysname> system-view

[Sysname] buffer egress cell queue 0 shared ratio 10


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_-617565909.htm -->

buffer queue guaranteed命令用来配置队列最多可使用的固定区域的比例。

undo buffer queue guaranteed命令用来取消指定队列最多可使用的固定区域的比例的配置。

【命令】

buffer egress [ slot slot-number ] cell queue queue-id guaranteed ratio ratio

undo buffer egress [ slot slot-number ] cell queue queue-id guaranteed

【缺省情况】

所有队列最多可使用的固定区域比例均为13%。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

egress：表示对发送数据缓冲区进行配置。

slot slot-number：表示设备在IRF中的成员编号。不指定该参数时，表示配置所有成员设备。

cell：配置队列最多可使用的cell资源中固定区域的比例。

queue-id：需要配置的队列编号，取值范围为0～7。

ratio ratio：队列最多可使用的缓存大小占整个接口板cell固定区域的大小的百分比。该参数的取值范围为0～100。

【使用指导】

缺省情况下，所有队列均分固定区域，但用户也可以使用该命令调整指定队列最多可使用的固定区域的比例，其它未配置的队列则均分剩余的固定区域。

配置该命令后，系统就与给队列预留指定大小的空间，即便该队列没有报文存储需求，其他队列也不能抢占。所有队列所配置的固定区域大小之和，不应超过可配置的总固定区域大小，否则配置失败。

数据缓冲区的配置比较复杂，而且对设备的转发功能有重要的影响，建议用户不要轻易修改数据缓冲区的参数。在需要较大的缓存空间时，建议使用Burst功能来自动分配缓冲区。

【举例】

\# 配置队列0最多可使用的cell固定区域的比例为整个cell固定缓冲区大小的20%。

<Sysname> system-view

[Sysname] buffer egress cell queue 0 guaranteed ratio 20


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_1713480194.htm -->

display buffer usage命令用来显示数据缓冲区的使用率。

【命令】

display buffer usage [ slot slot-number ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

slot slot-number：表示设备在IRF中的成员编号。不指定该参数时，表示所有成员设备。

【举例】

\# 显示数据缓冲区的使用率。

<Sysname> display buffer usage

Egress total-shared cell buffer usage on slot 1:

Total: 16061 KB

Used: 0 KB

Free: 16061 KB

 5sec 1min 5min

------------------------------------------------------------------

Block 1 0% 0% 0%

FGE9/0/1 0% 0% 0%

FGE9/0/2 0% 0% 0%

FGE9/0/3 0% 0% 0%

FGE9/0/4 0% 0% 0%

FGE9/0/5 0% 0% 0%

FGE9/0/6 0% 0% 0%

FGE9/0/7 0% 0% 0%

表1-2 display buffer usage命令显示信息描述表

| 5min | 过去5分钟以内该端口使用的缓冲区百分比例 |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_202315920.htm -->

display buffer命令用来显示数据缓冲区的比例。

【命令】

display buffer [ slot slot-number ] [ queue [ queue-id ] ]

【视图】

任意视图

【缺省用户角色】

network-admin

network-operator

【参数】

slot slot-number：表示设备在IRF中的成员编号。不指定该参数时，表示所有成员设备。

queue queue-id：显示队列最多可使用的固定区域的比例以及队列最多可使用的共享区域的比例，queue-id的取值范围为0～7。指定queue-id时，显示指定队列的相关信息；不指定queue-id时，显示所有队列的相关信息。未指定本参数时，显示共享区域的比例。

【举例】

\# 显示数据缓冲区的比例。

<Sysname> display buffer

Slot Type Eg(Total-shared)

1 cell 99

 Eg: Size of the sending buffer

Total-shared: Size of the shared buffer for all ports

 Unit: Ratio

\# 显示队列最多可使用的固定区域的比例以及队列最多可使用的共享区域的比例。

<Sysname> display buffer queue

Slot Queue Type Eg(Guaranteed, Shared)

1 0-7 cell 13, 88

 Eg: Size of the sending buffer

 Guaranteed: Size of the minimum guaranteed buffer per queue

 Shared: Size of the maximum shared buffer per queue

 Unit: Ratio

表1-1 display buffer命令显示信息描述表

| Unit | 数据缓冲区的单位，为%或byte |
| --- | --- |


---

<!-- 08-ACL和QoS命令参考/html/904213158_-1656791242_-876283664_2107543533.htm -->

buffer total-shared命令用来配置数据缓冲区中共享区域的比例。

undo buffer total-shared命令用来取消数据缓冲区中共享区域的比例的配置。

【命令】

buffer egress [ slot slot-number ] cell total-shared ratio ratio

undo buffer egress [ slot slot-number ] cell total-shared

【缺省情况】

cell缓冲区中共享区域所占比例为91%。

【视图】

系统视图

【缺省用户角色】

network-admin

【参数】

egress：表示对发送数据缓冲区进行配置。

slot slot-number：表示设备在IRF中的成员编号。不指定该参数时，表示配置所有成员设备。

cell：配置cell资源中的共享缓存区的比例。

ratio ratio：缓冲区中共享区域所占的比例，以百分数形式表示。该参数的取值范围为0～100。

【使用指导】

设备上整个数据缓冲区的大小是固定的，用户配置共享区域的大小后，其余部分将自动成为固定区域。

数据缓冲区的配置比较复杂，而且对设备的转发功能有重要的影响，建议用户不要轻易修改数据缓冲区的参数。在需要较大的缓存空间时，建议使用Burst功能来自动分配缓冲区。

【举例】

\# 配置当前设备cell资源中的共享区域所占比例为50%。

<Sysname> system-view

[Sysname] buffer egress cell total-shared ratio 50
