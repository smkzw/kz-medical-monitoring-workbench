#!/usr/bin/env python3
"""合成研究 listing 生成器：为测试轮产出真实感、内部逻辑自洽、含植入
医学线索的 Data Listing Excel（中文表头+英文列名，与真实交付形态一致）。

Profile 参数化（不同研究/适应症/访视/评分体系），布局形态覆盖
wide（行=记录）/ long（行=观测）/ matrix（列=访视）三种，供语义映射与
列签名推断的泛化验证。数据内置一致性规则与少量植入矛盾（AE分级 vs 化验
趋势、CM适应症 vs MH缺失、给药窗与随访完整性），供监查分析发现。

用法：
  python3 scripts/generate_test_listing.py --profile csu --out /tmp/test_materials/
  python3 scripts/generate_test_listing.py --profile pso --out /tmp/test_materials/
"""
from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook

random.seed(20260920)


class Profile:
    study_id: str
    study_title: str
    indication: str
    drug: str
    sites: tuple[str, ...]
    subjects_n: int
    visits: tuple[tuple[str, int], ...]  # (visit_code, day_offset)
    ctcae_version: str

    def term_pool(self) -> dict[str, list[str]]:
        raise NotImplementedError

    def scale_tables(self) -> list[dict]:
        raise NotImplementedError


class CsuProfile(Profile):
    study_id = "MG-K10-CSU-001"
    study_title = "MG-K10人源化单抗注射液治疗慢性自发性荨麻疹的III期研究"
    indication = "慢性自发性荨麻疹"
    drug = "MG-K10 300mg Q4W"
    sites = ("21", "22", "23", "24")
    subjects_n = 16
    visits = (("SCR", -14), ("R", 1), ("W2", 15), ("W4", 29), ("W8", 57), ("W12", 85), ("W16", 113), ("FU", 141))
    ctcae_version = "5.0"

    def term_pool(self) -> dict[str, list[str]]:
        return {
            "ae": ["头痛", "鼻咽炎", "上呼吸道感染", "注射部位红斑", "疲乏", "腹泻", "关节痛", "头晕", "咳嗽", "荨麻疹加重"],
            "mh": ["过敏性鼻炎", "哮喘", "甲状腺功能减退", "高血压", "胃炎", "慢性乙型肝炎携带", "偏头痛", "血脂异常"],
            "cm": ["氯雷他定", "西替利嗪", "奥马珠单抗", "孟鲁司特", "兰索拉唑", "左甲状腺素钠", "苯磺酸氨氯地平", "阿托伐他汀钙"],
        }


class PsoProfile(Profile):
    study_id = "CMS-D001-PSO-201"
    study_title = "CMS-D001治疗中重度斑块状银屑病的II期研究"
    indication = "中重度斑块状银屑病"
    drug = "CMS-D001 160mg Q2W"
    sites = ("31", "32", "33")
    subjects_n = 14
    visits = (("SCR", -21), ("R", 1), ("W4", 29), ("W8", 57), ("W12", 85), ("W16", 113), ("SAF_FU", 143))
    ctcae_version = "4.03"

    def term_pool(self) -> dict[str, list[str]]:
        return {
            "ae": ["鼻咽炎", "上呼吸道感染", "注射部位反应", "头痛", "ALT升高", "中性粒细胞计数降低", "关节痛", "瘙痒"],
            "mh": ["银屑病关节炎", "高脂血症", "2型糖尿病", "高血压", "脂肪肝", "结膜炎", "抑郁状态"],
            "cm": ["阿达木单抗", "甲氨蝶呤", "卡维地洛", "二甲双胍", "非诺贝特", "环孢素软胶囊"],
        }


PROFILES = {"csu": CsuProfile, "pso": PsoProfile}


def _rand_date(base: date, lo: int, hi: int) -> str:
    return (base + timedelta(days=random.randint(lo, hi))).isoformat()


def _pid(profile: Profile, i: int) -> str:
    site = profile.sites[i % len(profile.sites)]
    return f"{site}{i + 1:03d}"


def _sheet(wb: Workbook, name: str, cn_headers: list[str], en_headers: list[str], rows: list[list]) -> None:
    ws = wb.create_sheet(name)
    ws.append(cn_headers)
    ws.append(en_headers)
    for row in rows:
        ws.append(row)


def build(profile: Profile, out_dir: Path) -> Path:
    base = date(2026, 3, 2)
    subjects = [_pid(profile, i) for i in range(profile.subjects_n)]
    rnd = random.Random(hash(profile.study_id) % 2**31)
    terms = profile.term_pool()
    wb = Workbook()
    wb.remove(wb.active)

    mh_records: dict[str, list[str]] = {}
    ae_records: list[tuple[str, str, int]] = []

    # DM（wide）
    dm_rows = []
    for i, subj in enumerate(subjects):
        sex = "男" if i % 2 == 0 else "女"
        age = rnd.randint(18, 65)
        arm = "试验组" if i % 2 == 0 else "安慰剂组"
        rand_dt = _rand_date(base, 0, 30)
        dm_rows.append([subj, profile.sites[i % len(profile.sites)], sex, age, arm, rand_dt, "完成"])
    _sheet(wb, "DM", ["受试者编号", "中心编号", "性别", "年龄", "试验分组", "随机日期", "研究状态"],
           ["SUBJID", "SITEID", "SEX", "AGE", "ARM", "RANDDT", "COMPSTATUS"], dm_rows)

    # MH（wide）
    mh_rows = []
    for i, subj in enumerate(subjects):
        n_mh = rnd.randint(1, 3)
        for k in range(n_mh):
            term = terms["mh"][(i + k) % len(terms["mh"])]
            start = _rand_date(base - timedelta(days=400), 0, 300)
            ongoing = rnd.choice(["是", "否"])
            mh_rows.append([subj, f"M{len(mh_rows) + 1:03d}", term, start, ongoing, "既往病史"])
            mh_records.setdefault(subj, []).append(term)
    _sheet(wb, "MH", ["受试者编号", "病史记录号", "病史名称", "开始日期", "目前是否持续", "病史类型"],
           ["SUBJID", "MHNUM", "MHTERM", "MHSTDAT", "MHONGO", "MHCAT"], mh_rows)

    # AE（wide，含2处植入矛盾）
    ae_rows = []
    planted_plt_subject = subjects[2]
    for i, subj in enumerate(subjects):
        n_ae = rnd.randint(1, 4)
        for k in range(n_ae):
            term = terms["ae"][(i * 2 + k) % len(terms["ae"])]
            sev = rnd.choice(["1级", "2级", "3级"])
            start = _rand_date(base + timedelta(days=7), 0, 90)
            end = (date.fromisoformat(start) + timedelta(days=rnd.randint(2, 20))).isoformat()
            outcome = rnd.choice(["痊愈", "好转", "持续"])
            relate = rnd.choice(["肯定有关", "可能有关", "可能无关", "肯定无关"])
            ae_rows.append([subj, f"A{len(ae_rows) + 1:03d}", term, sev, start, end, outcome, relate, "否"])
            ae_records.append((subj, term, int(sev[0])))
    # 植入：血小板重度降低但化验仅轻度下降（分级与趋势矛盾）
    ae_rows.append([planted_plt_subject, f"A{len(ae_rows) + 1:03d}", "血小板计数降低", "3级",
                    (base + timedelta(days=40)).isoformat(), (base + timedelta(days=52)).isoformat(), "好转", "可能有关", "是"])
    ae_records.append((planted_plt_subject, "血小板计数降低", 3))
    _sheet(wb, "AE", ["受试者编号", "不良事件记录号", "不良事件名称", "严重程度", "开始日期", "结束日期", "转归", "与试验药物关系", "是否严重不良事件"],
           ["SUBJID", "AENUM", "AETERM", "AESEV", "AESTDAT", "AEENDAT", "AEOUT", "AEREL", "AESER"], ae_rows)

    # CM（wide，含1处植入：适应症引用哮喘但MH无哮喘）
    cm_rows = []
    cm_planted_subject = subjects[5]
    for i, subj in enumerate(subjects):
        n_cm = rnd.randint(1, 3)
        for k in range(n_cm):
            drug = terms["cm"][(i + k) % len(terms["cm"])]
            cm_rows.append([subj, f"C{len(cm_rows) + 1:03d}", drug, "既往用药", _rand_date(base - timedelta(days=200), 0, 150),
                            _rand_date(base, -30, -1), rnd.choice(["是", "否"])])
    cm_rows.append([cm_planted_subject, f"C{len(cm_rows) + 1:03d}", "孟鲁司特钠片", "哮喘病史长期用药",
                    _rand_date(base - timedelta(days=300), 0, 60), "", "是"])
    _sheet(wb, "CM", ["受试者编号", "合并用药记录号", "药物名称", "用药目的", "开始日期", "结束日期", "目前是否持续"],
           ["SUBJID", "CMNUM", "CMTRT", "CMINDC", "CMSTDAT", "CMENDAT", "CMONGO"], cm_rows)

    # EX 给药（long，按行=次给药）
    ex_rows = []
    for i, subj in enumerate(subjects):
        rand_dt = date.fromisoformat(dm_rows[i][5])
        dose_day = [1, 15, 29, 43, 57, 71, 85, 99] if isinstance(profile, CsuProfile) else [1, 15, 29, 43, 57, 71]
        for d in dose_day:
            dt = rand_dt + timedelta(days=d - 1)
            if dt > base + timedelta(days=130):
                continue
            ex_rows.append([subj, dt.isoformat(), profile.drug.split()[1] if " " in profile.drug else "Q4W",
                            profile.drug, rnd.choice(["完成", "完成", "完成", "延迟给药"])])
    _sheet(wb, "EX", ["受试者编号", "给药日期", "给药频次", "给药药物", "给药状态"],
           ["SUBJID", "EXDAT", "EXFRQ", "EXTRT", "EXSTATE"], ex_rows)

    # SV 访视（long）
    sv_rows = []
    for i, subj in enumerate(subjects):
        rand_dt = date.fromisoformat(dm_rows[i][5])
        for code, offset in profile.visits[1:]:
            sv_rows.append([subj, code, (rand_dt + timedelta(days=offset - 1)).isoformat(), rnd.choice(["已访视", "已访视", "已访视", "失约"])])
    _sheet(wb, "SV", ["受试者编号", "访视名称", "实际访视日期", "访视状态"],
           ["SUBJID", "VISIT", "VISDAT", "SVSTATE"], sv_rows)

    # 化验（long：行=观测，LB_CHEM 血常规节选；与植入AE匹配）
    lab_rows = []
    for i, subj in enumerate(subjects):
        rand_dt = date.fromisoformat(dm_rows[i][5])
        for code, offset in profile.visits[1:5]:
            dt = rand_dt + timedelta(days=offset - 1)
            plt = 215 - offset + rnd.randint(-15, 15)
            if subj == planted_plt_subject and code in ("W4", "W8"):
                plt = 118 if code == "W4" else 126  # 仅轻度下降 vs 3级AE（植入矛盾）
            lab_rows.append([subj, code, dt.isoformat(), "血小板计数", "10^9/L", plt, "125-350", "正常" if 125 <= plt <= 350 else "偏低"])
            lab_rows.append([subj, code, dt.isoformat(), "ALT", "U/L", rnd.randint(12, 38), "9-50", "正常"])
    _sheet(wb, "LB_HEM", ["受试者编号", "访视", "采样日期", "实验室指标名称", "单位", "结果", "参考范围", "临床意义"],
           ["SUBJID", "VISIT", "LBDAT", "LBTEST", "LBUNIT", "LBORRES", "LBREF", "LBSIGNI"], lab_rows)

    # 生命体征（wide行记录）
    vs_rows = []
    for i, subj in enumerate(subjects):
        for code, offset in profile.visits[1:5]:
            vs_rows.append([subj, code, rnd.randint(58, 96), rnd.randint(98, 140), rnd.randint(60, 88), rnd.randint(16, 22)])
    _sheet(wb, "VS", ["受试者编号", "访视", "心率次分", "收缩压mmHg", "舒张压mmHg", "呼吸次分"],
           ["SUBJID", "VISIT", "HRRATE", "SBP", "DBP", "RESP"], vs_rows)

    # 量表（matrix：列=访视；CSU=UAS7周评分；PSO=PASI评分）
    if isinstance(profile, CsuProfile):
        scale_cn = ["受试者编号", "W2周瘙痒评分", "W4周瘙痒评分", "W8周瘙痒评分", "W12周瘙痒评分"]
        scale_en = ["SUBJID", "UASW2", "UASW4", "UASW8", "UASW12"]
        scale_rows = [[s] + [rnd.randint(2, 20) for _ in range(4)] for s in subjects]
        _sheet(wb, "UAS", scale_cn, scale_en, scale_rows)
    else:
        scale_cn = ["受试者编号", "W4 PASI总分", "W8 PASI总分", "W12 PASI总分", "W16 PASI总分"]
        scale_en = ["SUBJID", "PASIW4", "PASIW8", "PASIW12", "PASIW16"]
        scale_rows = [[s] + [rnd.randint(4, 26) for _ in range(4)] for s in subjects]
        _sheet(wb, "PASI", scale_cn, scale_en, scale_rows)

    # 知情同意（名册形态：无临床日期/无术语列——应被通用排除）
    icf_rows = [[s, rnd.choice(["已签署", "已签署", "待签署"]), "v2.1"] for s in subjects]
    _sheet(wb, "ICF_TRACK", ["受试者编号", "知情状态", "知情版本"], ["SUBJID", "ICFSTATE", "ICFVER"], icf_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"【Data Listing】{profile.study_id}_合成测试数据_V1.0.xlsx"
    wb.save(out)
    print(f"generated: {out} ({len(wb.sheetnames)} sheets, {profile.subjects_n} subjects)")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--out", type=Path, default=Path("/tmp/test_materials"))
    args = parser.parse_args()
    build(PROFILES[args.profile](), args.out)


if __name__ == "__main__":
    main()
