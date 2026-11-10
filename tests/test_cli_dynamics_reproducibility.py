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
        outputs.append(json.loads(output.read_text())["trajectories"])
    assert outputs[0]==outputs[1]
    assert len(outputs[0])==12
    assert {row["replicate"] for row in outputs[0]}=={0,1}
    for row in outputs[0]:
        assert sum(row[k] for k in ("susceptible","exposed","infected","recovered"))==3
