#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
author: v_jbzhang
datetime: 2021/02/01
file: main.py

"""
import ipaddress

import httpx
import typer

try:
    from importlib import metadata
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata  # type: ignore

app = typer.Typer()

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"


@app.command()
def version():
    """
    显示版本号
    """

    typer.echo(__version__)
    typer.echo(f"{__package__} Installed as {__file__}")
    return __version__


@app.command()
def dnspod(
    token: str = typer.Option(..., envvar="DNSPOD_TOKEN"),
    domain: str = typer.Option(...),
    lang: str = typer.Option("en", help="返回的错误语言: [en,cn]"),
):
    """更新Dnspod(https://console.dnspod.cn/)上的解析记录"""
    try:
        package_name = metadata.metadata("Name")
        maintainer_email = metadata.metadata("maintainer_email")
    except metadata.PackageNotFoundError:
        package_name = "dddns"
        maintainer_email = "edsion@i1hao.com"
    ua = f"{package_name}/{__version__}({maintainer_email})"
    data = {"login_token": token, "format": "json", "lang": lang}
    domain_list = domain.split(".")
    if len(domain_list) == 2:
        data.update({"domain": "i1hao.com"})
    elif len(domain_list) <= 1:
        raise typer.Exit()
    else:
        data.update(
            {
                "domain": ".".join(domain_list[-2:]),
                "sub_domain": ".".join(domain_list[:-2]),
            }
        )
    with httpx.Client(headers={"User-Agent": ua}, http2=True, timeout=30) as client:
        query = client.post("https://dnsapi.cn/Record.List", data=data)
        query_res = query.json()
        if query_res.get("status", {}).get("code") != "1":
            raise typer.Exit()
        ip = client.get(
            "http://ifconfig.co/", headers={"User-Agent": "curl/7.64.1"}
        ).text.strip()

        if not ipaddress.ip_address(ip).is_global:
            raise typer.Exit()
        records = query_res.get("records")

        if len(records) <= 0:
            # TODO: 实现添加记录
            typer.secho("#TODO: 未实现添加记录功能", fg=typer.colors.RED, err=True)
            raise typer.Exit()
        for record in records:
            if record.get("value") == ip and record.get("enabled") == "1":
                typer.echo(query_res.get("status", {}).get("message"))
                break
            data.update(
                {
                    "record_id": record.get("id"),
                    "record_type": "A",
                    "record_line_id": record.get("line_id"),
                    "value": ip,
                }
            )
            update = client.post("https://dnsapi.cn/Record.Modify", data=data)
            update_res = update.json()
            if update_res.get("status", {}).get("code") == "1":
                typer.secho(
                    update_res.get("status", {}).get("message"), fg=typer.colors.YELLOW
                )
                break
            else:
                print("error")


if __name__ == "__main__":
    app()
