# bangumi 数据对接
0.该项目为CLI
1.使用本项目之前，你需要前往 https://next.bgm.tv/demo/access-token  获取Access Token，随后复制.env.template到.env 将token填入，如下示例
```env
BANGUMI_SWAGGER=https://bangumi.github.io/api/dist.json
BANGUMI_ACCESS_TOKEN=YOUR_OWN_ACCESS_TOKEN
```
2.使用`bangumi-crawer init`,会从BANGUMI_SWAGGER 获取dist.json ，并以此更新访问SDK
3.