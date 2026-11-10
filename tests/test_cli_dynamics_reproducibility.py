import json
import pytest
from py3plex import cli

@pytest.mark.parametrize("model,params", [("sir",["--gamma",".1"]),("sis",["--mu",".1"]),("seir",["--gamma",".1","--sigma",".2"])])
def test_cli_dynamics_seeded_counts_and_layers(model,params,tmp_path):
    network=tmp_path / "network.txt"
    network.write_text("A B social\nB C social\nA C work\n")
    outputs=[]
    for i in range(2):
        output=tmp_path / f"run{i}.json"
        assert cli.main(["dynamics",str(network),"--model",model,"--beta",".4",*params,"--steps","5","--replicates","2","--seed","42","--seed-nodes","A","--layers","social","--output",str(output)])==0
        data=json.loads(output.read_text())
        assert data["network"]["nodes"]==3
        assert data["network"]["layers"]==["social"]
        outputs.append(data["trajectories"])
    assert outputs[0]==outputs[1]
    assert len(outputs[0])==12
    assert {row["replicate"] for row in outputs[0]}=={0,1}
    for row in outputs[0]:
        assert sum(row[k] for k in ("susceptible","exposed","infected","recovered"))==3


def test_cli_dynamics_csv_and_plot(tmp_path):
    import csv
    network=tmp_path / "network.txt"
    network.write_text("A B social\nB C social\n")
    output=tmp_path / "result.csv"
    plot=tmp_path / "result.png"
    assert cli.main(["dynamics",str(network),"--model","sir","--beta",".3","--gamma",".1","--steps","2","--seed","42","--output",str(output),"--format","csv","--plot-file",str(plot)])==0
    with output.open() as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==3
    assert [int(row["step"]) for row in rows]==[0,1,2]
    assert plot.stat().st_size>0
