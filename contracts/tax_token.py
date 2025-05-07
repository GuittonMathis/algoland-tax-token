from pyteal import *

def approval_program():
    # Création : stocker Admin & Treasury
    on_creation = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        App.globalPut(Bytes("Admin"), Txn.application_args[0]),
        App.globalPut(Bytes("Treasury"), Txn.application_args[1]),
        Return(Int(1))
    ])

    # NoOp (taxe) : 3 txns groupées => net + taxe + appel app
    on_noop = Seq([
        # 1) Vérifier qu'il y a bien 3 tx dans le groupe
        Assert(Global.group_size() == Int(3)),

        # 2) Les deux premières tx doivent être des AssetTransfer
        Assert(Gtxn[0].type_enum() == TxnType.AssetTransfer),
        Assert(Gtxn[1].type_enum() == TxnType.AssetTransfer),

        # 3) Calculer et vérifier taxe = 9% du total
        #    taxe * 100 == (net + taxe) * 9
        Assert(
            Gtxn[1].asset_amount() * Int(100)
            == (Gtxn[0].asset_amount() + Gtxn[1].asset_amount()) * Int(9)
        ),

        # 4) S’assurer que la taxe va bien à la treasury
        Assert(
            Gtxn[1].asset_receiver()
            == App.globalGet(Bytes("Treasury"))
        ),

        # Tout est OK
        Return(Int(1))
    ])

    return Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.NoOp, on_noop],
    )

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    # Génération des TEAL
    with open("approval.teal", "w") as f:
        f.write(compileTeal(approval_program(), mode=Mode.Application, version=5))
    with open("clear.teal", "w") as f:
        f.write(compileTeal(clear_state_program(), mode=Mode.Application, version=5))
    print("✅ approval.teal et clear.teal générés")
