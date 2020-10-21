# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
 - Option to customize windows host (bios, networks, accounts and disks)
 - Create network interfaces using a list of MAC vendors.
 - Full import of hosts using the output of **extract-info.ps1** 
 - Building of custom SeaBIOS based on strings found in a real host.
 - Registration of ISO images to speed up the process of selecting a WIndows images for a host.
 - Automatization of the configuration of Elasticsearch, Sysmon and WinLogBeat.