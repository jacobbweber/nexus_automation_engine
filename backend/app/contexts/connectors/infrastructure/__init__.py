"""Connector infrastructure — concrete adapters implementing the domain ports.

The ``simulation`` package provides stateful, realistic adapters used pre-1.0 (and as the test
double for contract tests). Real adapters (AAP, Terraform CLI, ServiceNow, CyberArk, Dynatrace)
will live alongside them and satisfy the same ports.
"""
