#!/usr/bin/env python3
"""
tax_token.py

Generates the PyTeal approval and clear programs for the Dumbly ASA,
enforcing a 9% tax on each sell via a 3-transaction group.

On creation:
  • Stores Admin and Treasury addresses in global state.

On NoOp (sell):
  • Expects exactly 3 transactions:
      1. Asset transfer of net amount to buyer
      2. Asset transfer of tax amount (9%) to Treasury
      3. Application call to this contract
  • Validates the exact tax percentage and recipient.

Outputs:
  • approval.teal
  • clear.teal

Dependencies:
  pip install pyteal

Usage:
  python tax_token.py
"""

from pyteal import *

def approval_program():
    # When the app is created, save Admin & Treasury in global state
    on_creation = Seq(
        [
            Assert(Txn.application_args.length() == Int(2)),
            App.globalPut(Bytes("Admin"), Txn.application_args[0]),
            App.globalPut(Bytes("Treasury"), Txn.application_args[1]),
            Return(Int(1)),
        ]
    )

    # On normal call, enforce the 9% sell tax via an atomic group
    on_noop = Seq(
        [
            # 1) Ensure exactly 3 transactions in the group
            Assert(Global.group_size() == Int(3)),

            # 2) First two must be asset transfers
            Assert(Gtxn[0].type_enum() == TxnType.AssetTransfer),
            Assert(Gtxn[1].type_enum() == TxnType.AssetTransfer),

            # 3) Check tax: tax * 100 == total * 9
            Assert(
                Gtxn[1].asset_amount() * Int(100)
                == (Gtxn[0].asset_amount() + Gtxn[1].asset_amount()) * Int(9)
            ),

            # 4) Tax must go to the stored Treasury address
            Assert(Gtxn[1].asset_receiver() == App.globalGet(Bytes("Treasury"))),

            # All checks passed
            Return(Int(1)),
        ]
    )

    return Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.NoOp, on_noop],
    )

def clear_state_program():
    # Allow clear state without restrictions
    return Return(Int(1))

if __name__ == "__main__":
    # Compile and write out the TEAL programs
    with open("approval.teal", "w") as f:
        f.write(compileTeal(approval_program(), mode=Mode.Application, version=5))
    with open("clear.teal", "w") as f:
        f.write(compileTeal(clear_state_program(), mode=Mode.Application, version=5))
    print("✅ approval.teal and clear.teal generated")
