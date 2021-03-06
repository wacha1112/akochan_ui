import pathlib
import glob
import subprocess
import json

from .util import *
from .mjtypes import *

class Data_Processor:
    def __init__(self):
        self.x_discard = []
        self.y_discard = []

        self.x_chi = []
        self.y_chi = []

        self.x_pon = []
        self.y_pon = []

        self.x_daiminkan = []
        self.y_daiminkan = []

        self.x_kakan = []
        self.y_kakan = []

        self.x_ankan = []
        self.y_ankan = []

        self.x_reach = []
        self.y_reach = []

    def get_legal_moves(self, current_record):
        cmd = "./system.exe legal_action "
        input_json = {}
        input_json["record"] = current_record
        cmd += json.dumps(input_json, separators=(',', ':'))
        c = subprocess.check_output(cmd.split()).decode('utf-8').rstrip()
        return json.loads(c)

    def process_record(self, game_record, legal_actions_all):
        game_state = get_game_state_start_kyoku(json.loads(INITIAL_START_KYOKU))
        for i, action in enumerate(game_record):
            if action["type"] == "start_kyoku":
                game_state = get_game_state_start_kyoku(action)
            else:
                game_state.go_next_state(action)
            if action["type"] == "tsumo" or action["type"] == "chi" or action["type"] == "pon":
                if game_record[i+1]["type"] == "dahai" or game_record[i+1]["type"] == "reach":
                    x = game_state.to_numpy(action["actor"])
                    self.x_discard.append(x)

                    y = np.zeros(34, dtype=np.int)
                    i_dahai = i+1 if game_record[i+1]["type"] == "dahai" else i+2
                    hai = hai_str_to_int(game_record[i_dahai]["pai"])
                    y[get_hai34(hai)] = 1
                    self.y_discard.append(y)
            
            if action["type"] == "tsumo" or action["type"] == "dahai":
                for legal_action in legal_actions_all[i]:
                    if legal_action["type"] == "chi":
                        if ((game_record[i+1]["type"] == "hora" and game_record[i+1]["actor"] != legal_action["actor"]) or
                            (game_record[i+1]["type"] == "pon" and game_record[i+1]["actor"] != legal_action["actor"]) or
                            (game_record[i+1]["type"] == "daiminkan" and game_record[i+1]["actor"] != legal_action["actor"])):
                            continue
                        x = game_state.to_numpy(legal_action["actor"])
                        self.x_chi.append(x)
                        self.y_chi.append(1 if legal_action == game_record[i+1] else 0)
                    if legal_action["type"] == "pon":
                        if game_record[i+1]["type"] == "hora" and game_record[i+1]["actor"] != legal_action["actor"]:
                            continue
                        x = game_state.to_numpy(legal_action["actor"])
                        self.x_pon.append(x)
                        self.y_pon.append(1 if legal_action == game_record[i+1] else 0)
                    if legal_action["type"] == "daiminkan":
                        if game_record[i+1]["type"] == "hora" and game_record[i+1]["actor"] != legal_action["actor"]:
                            continue
                        x = game_state.to_numpy(legal_action["actor"])
                        self.x_daiminkan.append(x)
                        self.y_daiminkan.append(1 if legal_action == game_record[i+1] else 0)
                    if legal_action["type"] == "kakan":
                        x = game_state.to_numpy(legal_action["actor"])
                        self.x_kakan.append(x)
                        self.y_kakan.append(1 if legal_action == game_record[i+1] else 0)
                    if legal_action["type"] == "ankan":
                        x = game_state.to_numpy(legal_action["actor"])
                        self.x_ankan.append(x)
                        self.y_ankan.append(1 if legal_action == game_record[i+1] else 0)
                    if legal_action["type"] == "reach":
                        x = game_state.to_numpy(legal_action["actor"])
                        self.x_reach.append(x)
                        self.y_reach.append(1 if legal_action == game_record[i+1] else 0)

    def dump_child(self, dir_path, tenhou_id, action_type, X, Y):
        if 0 < len(Y):
            out_dir_pathstr = dir_path + "/" + action_type + "/" + tenhou_id[:4] + "/" + tenhou_id[:8]
            out_dir = pathlib.Path(out_dir_pathstr)
            if not out_dir.is_dir():
                out_dir.mkdir(parents=True)
            np.savez_compressed(out_dir_pathstr + "/" + action_type + "_" + tenhou_id, X, Y)
            X.clear()
            Y.clear()

    def dump(self, dir_path, tenhou_id):
        self.dump_child(dir_path, tenhou_id, "discard", self.x_discard, self.y_discard)
        self.dump_child(dir_path, tenhou_id, "chi", self.x_chi, self.y_chi)
        self.dump_child(dir_path, tenhou_id, "pon", self.x_pon, self.y_pon)
        self.dump_child(dir_path, tenhou_id, "daiminkan", self.x_daiminkan, self.y_daiminkan)
        self.dump_child(dir_path, tenhou_id, "kakan", self.x_kakan, self.y_kakan)
        self.dump_child(dir_path, tenhou_id, "ankan", self.x_ankan, self.y_ankan)
        self.dump_child(dir_path, tenhou_id, "reach", self.x_reach, self.y_reach)

    def dump_normal_child(self, dir_path, name_str, action_type, X, Y):
        if 0 < len(Y):
            out_dir_pathstr = dir_path + "/" + action_type + "/" + name_str
            out_dir = pathlib.Path(out_dir_pathstr)
            if not out_dir.is_dir():
                out_dir.mkdir(parents=True)
            np.savez_compressed(out_dir_pathstr + "/" + action_type + "_" + name_str, X, Y)
            X.clear()
            Y.clear()

    def dump_normal(self, dir_path, name_str):
        self.dump_normal_child(dir_path, name_str, "discard", self.x_discard, self.y_discard) 

def proc_tenhou_mjailog(tenhou_id):
    dp = Data_Processor()
    log_path_str = "tenhou_mjailog/" + tenhou_id[:4] + "/" + tenhou_id[:8] + "/" + tenhou_id + ".json"
    game_record = read_log_json(log_path_str)
    cmd = "./system.exe legal_action_log_all " + log_path_str
    c = subprocess.check_output(cmd.split()).decode('utf-8').rstrip()
    legal_actions_all = json.loads(c)
    dp.process_record(game_record, legal_actions_all)
    dp.dump("tenhou_npz", tenhou_id)

def proc_batch_tenhou_mjailog(prefix, update):
    if len(prefix) < 4:
        print("proc_batch_tenhou_mjailog prefix too short")
        return
    target = ""
    if len(prefix) <= 8:
        target = "tenhou_mjailog/" + prefix[:4] + "/" + prefix + "*/*.json"
    else:
        target = "tenhou_mjailog/" + prefix[:4] + "/" + prefix[:8] + "/" + prefix + "*.json"

    file_list = glob.glob(target)
    for file_name in file_list:
        file_name = file_name.replace('\\', '/')
        tenhou_id = file_name.split('/')[-1].split('.')[0]

        if not update:
            discard_path = pathlib.Path("tenhou_npz/discard/" + tenhou_id[:4] + "/" + tenhou_id[:8] + "/discard_" + tenhou_id + ".npz")
            if discard_path.is_file():
                continue

        print("process:", tenhou_id)
        proc_tenhou_mjailog(tenhou_id)  
    