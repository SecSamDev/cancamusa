from jinja2 import Template
import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from ad_struct import ADStructure


with open(os.path.join(os.path.dirname(__file__), '../lib/scripter/templates/fill-ad.ps1.jinja'),'r') as fill_ad:
    template = Template(fill_ad.read())

    dc_domain = "cancamusa.com"

    dc_path = dc_domain.split(".")

    dc_path_string = "DC=" + (",DC=".join(dc_path))

    ad_structure = {
        "domain" : dc_domain,
        "ou" : {
            "IT-Services" : {
                "name" : "IT-Services",
                "ou" : {
                    "SupportGroups" : {
                        "name" : "SupportGroups",
                        "ou" : {
                            "CostCenter" : {
                                "name" : "CostCenter",
                                "ou" : {

                                },
                                "groups" : {
                                    "CostCenter-123" : {
                                        "name" : "CostCenter-123",
                                        "sam_account_name" : "CostCenter-123",
                                        "group_category" : "Security",
                                        "group_scope" : "Global",
                                        "display_name" : "CostCenter 123"
                                    },
                                    "CostCenter-125" : {
                                        "name" : "CostCenter-125",
                                        "sam_account_name" : "CostCenter-125",
                                        "group_category" : "Security",
                                        "group_scope" : "Global",
                                        "display_name" : "CostCenter 125"
                                    }
                                }
                            }
                        },
                        "groups" : {
                            "SecurePrinting" : {
                                "name" : "SecurePrinting",
                                "sam_account_name" : "SecurePrinting",
                                "group_category" : "Security",
                                "group_scope" : "Global",
                                "display_name" : "Secure Printing Users"
                            }
                        }
                    }
                },
                "groups" : {
                    
                }
            },
            "Locations" : {
                "name" : "Locations",
                "ou" : {
                    "HeadQuarter" : {
                        "name" : "HeadQuarter",
                        "ou" : {
                            "Users" : {
                                "name" : "Users",
                                "groups" : {},
                                "ou" : {}
                            }
                        },
                        "groups" : {}
                    }
                },
                "groups" : {}
            }
        }
    }
    struct = ADStructure.from_json(ad_structure)


    ad_groups = struct.list_groups()
    ad_ous = struct.list_child_ou()

    user_list = [
        {
            "sam_account_name" : "samuel.garces",
            "UserPrincipalName" : "samuel.garces@cancamusa.com",
            "Firstname" : "Samuel",
            "Lastname" : "Garces",
            "Department" : "CyberSecurity",
            "ou" : "HeadQuarter",
            "Password" : "contoso"
        },
        {
            "sam_account_name" : "canca.musa",
            "UserPrincipalName" : "canca.musa@cancamusa.com",
            "Firstname" : "Canca",
            "Lastname" : "Musa",
            "Department" : "CyberSecurity",
            "ou" : "HeadQuarter",
            "Password" : "contoso"
        }
    ]
    print(template.render(user_list=user_list, ad_groups=ad_groups, ad_ous= ad_ous))


