import itertools

from iteround import saferound

cpus_dict = dict()
cpus_dict.update(
    dict.fromkeys(["JUMP3", "LOCPCACMI", "NONLINEARODES", "GRNVBEM", "CMI2NI"], 4)
)
cpus_dict.update(
    dict.fromkeys(
        [
            "TIGRESS",
            "PCACMI",
            "PLSNET",
            "INFERELATOR",
            "GENIE3_RF",
            "GRNBOOST2",
            "GENIE3_ET",
        ],
        3,
    )
)
cpus_dict.update(dict.fromkeys(["KBOOST", "LEAP"], 2))
cpus_dict.update(
    dict.fromkeys(
        [
            "ARACNE",
            "BC3NET",
            "C3NET",
            "CLR",
            "MRNET",
            "MRNETB",
            "PCIT",
            "MEOMI",
            "NARROMI",
            "RSNET",
            "PIDC",
            "PUC",
        ],
        1,
    )
)


def get_optimal_cpu_distribution(tecs, cores_ids):
    """Obtain a balanced CPU assignment for a set of inference techniques."""

    cpus_list = []
    for tec in tecs:
        cpus_list.append(cpus_dict.get(tec))

    groups = []
    group_sums = []
    for cpu in set(cpus_list):
        members = [i for i in range(len(cpus_list)) if cpus_list[i] == cpu]
        groups.append(members)
        group_sums.append(len(members) * cpu)

    scaled_groups_sums = [
        (gsum / sum(group_sums)) * len(cores_ids) for gsum in group_sums
    ]

    if 1 in set(cpus_list):
        cpus_set_list = list(set(cpus_list))
        idx_group_of_ones = cpus_set_list.index(1)

        factor = (
            1
            if len(cores_ids) > sum(cpus_list)
            else min(
                0.5,
                (scaled_groups_sums[idx_group_of_ones] / group_sums[idx_group_of_ones])
                / 2,
            )
        )
        ones_sum = group_sums[idx_group_of_ones] * factor
        surplus = scaled_groups_sums[idx_group_of_ones] - ones_sum
        scaled_groups_sums[idx_group_of_ones] = ones_sum

        cpus_set_list[idx_group_of_ones] = 0
        surplus_distributed = [
            (cpu / max(1, sum(cpus_set_list))) * surplus for cpu in cpus_set_list
        ]
        scaled_groups_sums = [
            sum(x) for x in zip(scaled_groups_sums, surplus_distributed)
        ]

    safe_groups_sums = saferound(scaled_groups_sums, places=0)

    cpus_cnt = 0
    res = dict.fromkeys(tecs, list())
    for idx_group in range(len(groups)):
        cpus_group = int(safe_groups_sums[idx_group])
        cpus_ids = (
            cores_ids[cpus_cnt : (cpus_group + cpus_cnt)]
            if cpus_group != 0
            else [cores_ids[max(0, cpus_group - 1)]]
        )
        cpus_cnt += cpus_group

        members = groups[idx_group]

        if len(members) < len(cpus_ids):
            cycle_members = itertools.cycle(members)
            for cpu_id in cpus_ids:
                member = next(cycle_members)
                res[tecs[member]] = res[tecs[member]] + [cpu_id]
        else:
            cpus_ids = itertools.cycle(cpus_ids)
            for member in members:
                res[tecs[member]] = res[tecs[member]] + [next(cpus_ids)]

    return res


__all__ = ["get_optimal_cpu_distribution"]
