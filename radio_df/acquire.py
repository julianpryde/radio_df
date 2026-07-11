"""Coherent IQ acquisition from the multi-channel SDR receiver.

Wraps the receiver's streaming interface and yields aligned multi-channel
sample blocks for the rest of the pipeline. (Phase 5 work; hardware options
are listed in PLAN.md.)
"""
