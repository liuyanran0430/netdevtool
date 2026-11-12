import type { ThemeConfig } from 'antd'

export const appTheme: ThemeConfig = {
  token: {
    colorPrimary: '#3268DB',
    colorInfo: '#3268DB',
    colorSuccess: '#29826D',
    colorWarning: '#B47B24',
    colorError: '#C45C60',
    colorText: '#202C40',
    colorTextSecondary: '#647289',
    colorBorder: '#E4EAF2',
    colorBorderSecondary: '#EDF1F7',
    borderRadius: 8,
    controlHeight: 36,
    fontSize: 13,
    fontFamily:
      "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif",
    boxShadowSecondary: '0 8px 24px rgba(32, 44, 64, 0.08)',
  },
  components: {
    Button: {
      primaryShadow: 'none',
      defaultShadow: 'none',
      fontWeight: 500,
    },
    Checkbox: {
      borderRadiusSM: 3,
    },
    Input: {
      activeShadow: '0 0 0 2px rgba(50, 104, 219, 0.08)',
    },
    Drawer: {
      paddingLG: 0,
    },
  },
}
