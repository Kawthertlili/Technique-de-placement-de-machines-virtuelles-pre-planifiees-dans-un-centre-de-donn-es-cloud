import random
import tkinter as tk
from tkinter import scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import time
import re  # Ajout pour l'extraction robuste des numéros

def generate_machines(n_physiques, vm_min, vm_max, step, n_scenarios):
    machines_physiques = []
    machines_virtuelles_list = [[] for _ in range(n_scenarios)]
    
    for i in range(n_physiques):
        machines_physiques.append([f"PM_{i+1}", random.randint(16, 32), random.randint(32, 128), random.randint(500, 1000)])
    
    for idx in range(n_scenarios):
        n_virt = random.randrange(vm_min, vm_max + 1, step)
        for i in range(n_virt):
            arrival = random.randint(0, 1440)
            departure = random.randint(arrival, 1440)
            machines_virtuelles_list[idx].append([f"VM_{idx+1}_{i+1}", random.randint(1, 8), random.randint(1, 32), random.randint(10, 200), arrival, departure])
    
    return machines_physiques, machines_virtuelles_list

def save_to_txt(filename, machines):
    with open(filename, mode='w') as file:
        for machine in machines:
            file.write(" ".join(map(str, machine)) + "\n")

def read_from_txt(filename, is_vm=False):
    machines = []
    with open(filename, mode='r') as file:
        for line in file:
            parts = line.strip().split()
            if is_vm:
                machines.append([parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])])
            else:
                machines.append([parts[0], int(parts[1]), int(parts[2]), int(parts[3])])
    return machines

def is_feasible(pm, vm, assigned_vms):
    remaining_cpu = pm[1]
    remaining_ram = pm[2]
    remaining_storage = pm[3]
    
    for assigned_vm in assigned_vms:
        if vm[4] < assigned_vm[5] and vm[5] > assigned_vm[4]:
            remaining_cpu -= assigned_vm[1]
            remaining_ram -= assigned_vm[2]
            remaining_storage -= assigned_vm[3]
    
    return remaining_cpu >= vm[1] and remaining_ram >= vm[2] and remaining_storage >= vm[3]

def initial_placement(vms, pms):
    placement = {pm[0]: [] for pm in pms}
    unplaced_vms = []
    
    vms.sort(key=lambda x: x[4])
    
    for vm in vms:
        placed = False
        for pm in pms:
            if is_feasible(pm, vm, placement[pm[0]]):
                placement[pm[0]].append(vm)
                placed = True
                break
        if not placed:
            unplaced_vms.append(vm)
    
    return placement, unplaced_vms

def evaluate(placement):
    return sum(len(vms) for vms in placement.values())

def tabu_search(vms, pms, iterations=100, tabu_size=10):
    best_solution, unplaced_vms = initial_placement(vms, pms)
    best_score = evaluate(best_solution)
    tabu_list = []
    
    for _ in range(iterations):
        neighbors = []
        
        for vm in vms:
            if any(vm[0] in [v[0] for v in vms_list] for vms_list in best_solution.values()):
                continue
            
            for pm in pms:
                new_solution = {key: value[:] for key, value in best_solution.items()}
                if is_feasible(pm, vm, new_solution[pm[0]]):
                    new_solution[pm[0]].append(vm)
                    if new_solution not in tabu_list:
                        neighbors.append((new_solution, evaluate(new_solution)))
        
        if not neighbors:
            continue
        
        best_neighbor = max(neighbors, key=lambda x: x[1])
        
        if best_neighbor[1] > best_score:
            best_solution, best_score = best_neighbor
            tabu_list.append(best_solution)
            if len(tabu_list) > tabu_size:
                tabu_list.pop(0)
    
    final_unplaced_vms = [vm for vm in vms if all(vm[0] not in [v[0] for v in vms_list] for vms_list in best_solution.values())]
    return best_solution, final_unplaced_vms, best_score

def calculate_resource_usage(placement, pms):
    resource_usage = {}
    for pm in pms:
        pm_name = pm[0]
        vms = placement[pm_name]
        
        timeline = []
        for vm in vms:
            timeline.append((vm[4], 'start', vm[1], vm[2], vm[3]))
            timeline.append((vm[5], 'end', vm[1], vm[2], vm[3]))
        
        timeline.sort(key=lambda x: x[0])
        
        max_cpu = pm[1]
        max_ram = pm[2]
        max_storage = pm[3]
        
        current_cpu = 0
        current_ram = 0
        current_storage = 0
        max_observed_cpu = 0
        max_observed_ram = 0
        max_observed_storage = 0
        
        for event in timeline:
            time, typ, cpu, ram, storage = event
            if typ == 'start':
                current_cpu += cpu
                current_ram += ram
                current_storage += storage
            else:
                current_cpu -= cpu
                current_ram -= ram
                current_storage -= storage
            
            max_observed_cpu = max(max_observed_cpu, current_cpu)
            max_observed_ram = max(max_observed_ram, current_ram)
            max_observed_storage = max(max_observed_storage, current_storage)
        
        cpu_percent = min((max_observed_cpu / max_cpu) * 100, 100) if max_cpu > 0 else 0
        ram_percent = min((max_observed_ram / max_ram) * 100, 100) if max_ram > 0 else 0
        storage_percent = min((max_observed_storage / max_storage) * 100, 100) if max_storage > 0 else 0
        
        resource_usage[pm_name] = {
            'cpu': cpu_percent,
            'ram': ram_percent,
            'storage': storage_percent,
            'vms': [vm[0] for vm in vms],
            'max_cpu': max_cpu,
            'max_ram': max_ram,
            'max_storage': max_storage,
            'used_cpu': max_observed_cpu,
            'used_ram': max_observed_ram,
            'used_storage': max_observed_storage
        }
    
    return resource_usage

def create_graph_window(fig, title):
    graph_window = tk.Toplevel(root)
    graph_window.title(title)
    
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    close_button = tk.Button(graph_window, text="Fermer", command=graph_window.destroy)
    close_button.pack()

def plot_cpu_usage(pm_names, cpu_usage, resource_usage, pms, scenario_num):
    fig = plt.figure(figsize=(8, 5))
    plt.title(f"Scénario {scenario_num} - Utilisation du CPU", fontsize=14)
    bars_usage = plt.bar(pm_names, cpu_usage, color='skyblue', label='Utilisation')
    bars_capacity = plt.bar(pm_names, [100]*len(pm_names), color='none', edgecolor='gray', linewidth=2, alpha=0.5, label='Capacité max')
    plt.ylabel('CPU (%)')
    plt.legend()
    for bar, usage, pm in zip(bars_usage, cpu_usage, pms):
        usage_text = f"{usage:.1f}%\n({resource_usage[pm[0]]['used_cpu']}/{pm[1]})"
        plt.text(bar.get_x() + bar.get_width()/2, min(usage, 100)/2, 
                usage_text, ha='center', va='center', color='black')
    plt.tight_layout()
    create_graph_window(fig, f"CPU - Scénario {scenario_num}")

def plot_ram_usage(pm_names, ram_usage, resource_usage, pms, scenario_num):
    fig = plt.figure(figsize=(8, 5))
    plt.title(f"Scénario {scenario_num} - Utilisation de la RAM", fontsize=14)
    bars_usage = plt.bar(pm_names, ram_usage, color='lightgreen', label='Utilisation')
    bars_capacity = plt.bar(pm_names, [100]*len(pm_names), color='none', edgecolor='gray', linewidth=2, alpha=0.5, label='Capacité max')
    plt.ylabel('RAM (%)')
    plt.legend()
    for bar, usage, pm in zip(bars_usage, ram_usage, pms):
        usage_text = f"{usage:.1f}%\n({resource_usage[pm[0]]['used_ram']}/{pm[2]})"
        plt.text(bar.get_x() + bar.get_width()/2, min(usage, 100)/2, 
                usage_text, ha='center', va='center', color='black')
    plt.tight_layout()
    create_graph_window(fig, f"RAM - Scénario {scenario_num}")

def plot_storage_usage(pm_names, storage_usage, resource_usage, pms, scenario_num):
    fig = plt.figure(figsize=(8, 5))
    plt.title(f"Scénario {scenario_num} - Utilisation du Stockage", fontsize=14)
    bars_usage = plt.bar(pm_names, storage_usage, color='salmon', label='Utilisation')
    bars_capacity = plt.bar(pm_names, [100]*len(pm_names), color='none', edgecolor='gray', linewidth=2, alpha=0.5, label='Capacité max')
    plt.ylabel('Stockage (%)')
    plt.legend()
    for bar, usage, pm in zip(bars_usage, storage_usage, pms):
        usage_text = f"{usage:.1f}%\n({resource_usage[pm[0]]['used_storage']}/{pm[3]})"
        plt.text(bar.get_x() + bar.get_width()/2, min(usage, 100)/2, 
                usage_text, ha='center', va='center', color='black')
    plt.tight_layout()
    create_graph_window(fig, f"Stockage - Scénario {scenario_num}")

def plot_vm_counts(pm_names, vm_counts, scenario_num):
    fig = plt.figure(figsize=(8, 5))
    plt.title(f"Scénario {scenario_num} - Nombre de VMs", fontsize=14)
    plt.plot(pm_names, vm_counts, 'o-', color='purple')
    plt.ylabel('Nombre de VMs')
    for x, y in zip(pm_names, vm_counts):
        plt.text(x, y, str(y), ha='center', va='bottom')
    plt.tight_layout()
    create_graph_window(fig, f"VMs - Scénario {scenario_num}")

def plot_resource_usage(placement, pms, scenario_num):
    if not placement:
        return
    
    plt.close('all')
    
    pm_names = [pm[0] for pm in pms]
    cpu_usage = []
    ram_usage = []
    storage_usage = []
    vm_counts = []
    
    resource_usage = calculate_resource_usage(placement, pms)
    
    for pm in pms:
        pm_name = pm[0]
        usage = resource_usage[pm_name]
        cpu_usage.append(usage['cpu'])
        ram_usage.append(usage['ram'])
        storage_usage.append(usage['storage'])
        vm_counts.append(len(usage['vms']))
    
    plot_cpu_usage(pm_names, cpu_usage, resource_usage, pms, scenario_num)
    plot_ram_usage(pm_names, ram_usage, resource_usage, pms, scenario_num)
    plot_storage_usage(pm_names, storage_usage, resource_usage, pms, scenario_num)
    plot_vm_counts(pm_names, vm_counts, scenario_num)

def plot_rejection_rates(rejection_rates):
    if not rejection_rates:
        return
    
    plt.close('all')
    
    fig = plt.figure(figsize=(10, 6))
    plt.title("Taux de rejet par scénario", fontsize=16)
    
    scenarios = range(1, len(rejection_rates)+1)
    plt.bar(scenarios, rejection_rates, color='red', alpha=0.7)
    
    for i, rate in enumerate(rejection_rates):
        plt.text(i+1, rate+1, f"{rate:.1f}%", ha='center')
    
    plt.xlabel("Scénario")
    plt.ylabel("Taux de rejet (%)")
    plt.xticks(scenarios)
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    avg_rejection = sum(rejection_rates) / len(rejection_rates)
    plt.axhline(y=avg_rejection, color='blue', linestyle='--', label=f"Moyenne: {avg_rejection:.1f}%")
    plt.legend()
    
    create_graph_window(fig, "Taux de rejet par scénario")

def on_submit():
    try:
        submit_button.config(state=tk.DISABLED)
        load_button.config(state=tk.DISABLED)
        
        n_physiques = int(entry_n_physiques.get())
        vm_min = int(entry_vm_min.get())
        vm_max = int(entry_vm_max.get())
        step = int(entry_step.get())
        n_scenarios = int(entry_n_scenarios.get())
        
        if vm_min > vm_max:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Erreur: Le minimum ne peut pas être supérieur au maximum.\n")
            submit_button.config(state=tk.NORMAL)
            load_button.config(state=tk.NORMAL)
            return
        if step <= 0:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Erreur: Le pas doit être un entier positif.\n")
            submit_button.config(state=tk.NORMAL)
            load_button.config(state=tk.NORMAL)
            return
        
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Génération des scénarios en cours...\n")
        root.update_idletasks()
        
        timestamp = int(time.time())
        scenario_folder = f"scenarios_{timestamp}"
        os.makedirs(scenario_folder, exist_ok=True)
        
        pms, vms_list = generate_machines(n_physiques, vm_min, vm_max, step, n_scenarios)
        save_to_txt(f"{scenario_folder}/machines_physiques.txt", pms)
        
        rejection_rates = []
        avg_cpu_usage = []
        avg_ram_usage = []
        avg_storage_usage = []
        
        for idx, vms in enumerate(vms_list, start=1):  # Modification ici: start=1
            if not root.winfo_exists():
                return
                
            filename = f"{scenario_folder}/machines_virtuelles_{idx}.txt"
            save_to_txt(filename, vms)
            
            result_text.insert(tk.END, f"\n=== Scénario {idx} ===\n")
            result_text.insert(tk.END, f"Nombre de VMs générées: {len(vms)}\n")
            root.update_idletasks()
            
            vms_from_file = read_from_txt(filename, is_vm=True)
            best_solution, unplaced_vms, best_score = tabu_search(vms_from_file, pms)
            
            total_vms = len(vms_from_file)
            rejected_vms = len(unplaced_vms)
            rejection_rate = (rejected_vms / total_vms) * 100 if total_vms > 0 else 0
            rejection_rates.append(rejection_rate)
            
            resource_usage = calculate_resource_usage(best_solution, pms)
            
            scenario_cpu = []
            scenario_ram = []
            scenario_storage = []
            
            result_text.insert(tk.END, "\nDétail des PMs:\n")
            for pm in pms:
                if not root.winfo_exists():
                    return
                    
                pm_name = pm[0]
                usage = resource_usage.get(pm_name, {'cpu': 0, 'ram': 0, 'storage': 0, 'vms': []})
                
                scenario_cpu.append(usage['cpu'])
                scenario_ram.append(usage['ram'])
                scenario_storage.append(usage['storage'])
                
                result_text.insert(tk.END, f"\n{pm_name}:\n")
                result_text.insert(tk.END, f"- CPU utilisé: {usage['cpu']:.2f}% ({usage['used_cpu']}/{pm[1]})\n")
                result_text.insert(tk.END, f"- RAM utilisée: {usage['ram']:.2f}% ({usage['used_ram']}/{pm[2]})\n")
                result_text.insert(tk.END, f"- Stockage utilisé: {usage['storage']:.2f}% ({usage['used_storage']}/{pm[3]})\n")
                result_text.insert(tk.END, f"- VMs placées: {', '.join(usage['vms']) if usage['vms'] else 'Aucune'}\n")
                root.update_idletasks()
            
            avg_cpu = sum(scenario_cpu) / len(scenario_cpu) if scenario_cpu else 0
            avg_ram = sum(scenario_ram) / len(scenario_ram) if scenario_ram else 0
            avg_storage = sum(scenario_storage) / len(scenario_storage) if scenario_storage else 0
            
            avg_cpu_usage.append(avg_cpu)
            avg_ram_usage.append(avg_ram)
            avg_storage_usage.append(avg_storage)
            
            result_text.insert(tk.END, f"\nRésumé pour le scénario {idx}:\n")
            result_text.insert(tk.END, f"- Nombre de VMs placées: {best_score}\n")
            result_text.insert(tk.END, f"- Nombre de VMs rejetées: {rejected_vms}\n")
            result_text.insert(tk.END, f"- Taux de rejet: {rejection_rate:.2f}%\n")
            result_text.insert(tk.END, f"- CPU moyen utilisé: {avg_cpu:.2f}%\n")
            result_text.insert(tk.END, f"- RAM moyenne utilisée: {avg_ram:.2f}%\n")
            result_text.insert(tk.END, f"- Stockage moyen utilisé: {avg_storage:.2f}%\n")
            root.update_idletasks()
            
            plot_resource_usage(best_solution, pms, idx)
        
        if rejection_rates and root.winfo_exists():
            avg_rejection = sum(rejection_rates) / len(rejection_rates)
            global_avg_cpu = sum(avg_cpu_usage) / len(avg_cpu_usage)
            global_avg_ram = sum(avg_ram_usage) / len(avg_ram_usage)
            global_avg_storage = sum(avg_storage_usage) / len(avg_storage_usage)
            
            result_text.insert(tk.END, "\n=== Résultats globaux ===\n")
            result_text.insert(tk.END, f"Taux de rejet moyen: {avg_rejection:.2f}%\n")
            result_text.insert(tk.END, f"CPU moyen utilisé: {global_avg_cpu:.2f}%\n")
            result_text.insert(tk.END, f"RAM moyenne utilisée: {global_avg_ram:.2f}%\n")
            result_text.insert(tk.END, f"Stockage moyen utilisé: {global_avg_storage:.2f}%\n")
            
            plot_rejection_rates(rejection_rates)
        
    except Exception as e:
        if root.winfo_exists():
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"Erreur: {str(e)}\n")
    finally:
        if root.winfo_exists():
            submit_button.config(state=tk.NORMAL)
            load_button.config(state=tk.NORMAL)

def load_existing_scenarios():
    try:
        submit_button.config(state=tk.DISABLED)
        load_button.config(state=tk.DISABLED)
        
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Chargement des scénarios existants...\n")
        root.update_idletasks()
        
        if not os.path.exists("machines_physiques.txt"):
            result_text.insert(tk.END, "Erreur: Fichier machines_physiques.txt introuvable\n")
            return
            
        pms = read_from_txt("machines_physiques.txt", is_vm=False)
        
        rejection_rates = []
        avg_cpu_usage = []
        avg_ram_usage = []
        avg_storage_usage = []
        
        # Nouvelle méthode robuste pour détecter et trier les fichiers
        vm_files = []
        for f in os.listdir():
            match = re.match(r'machines_virtuelles_(\d+)\.txt', f)
            if match:
                try:
                    num = int(match.group(1))
                    vm_files.append((num, f))
                except:
                    continue
        
        # Tri par numéro de scénario en ordre croissant
        vm_files.sort(key=lambda x: x[0])
        
        for num, vm_file in vm_files:
            if not root.winfo_exists():
                return
                
            result_text.insert(tk.END, f"\n=== Scénario {num} ===\n")
            
            vms_from_file = read_from_txt(vm_file, is_vm=True)
            result_text.insert(tk.END, f"Nombre de VMs chargées: {len(vms_from_file)}\n")
            root.update_idletasks()
            
            best_solution, unplaced_vms, best_score = tabu_search(vms_from_file, pms)
            
            total_vms = len(vms_from_file)
            rejected_vms = len(unplaced_vms)
            rejection_rate = (rejected_vms / total_vms) * 100 if total_vms > 0 else 0
            rejection_rates.append(rejection_rate)
            
            resource_usage = calculate_resource_usage(best_solution, pms)
            
            scenario_cpu = []
            scenario_ram = []
            scenario_storage = []
            
            result_text.insert(tk.END, "\nDétail des PMs:\n")
            for pm in pms:
                if not root.winfo_exists():
                    return
                    
                pm_name = pm[0]
                usage = resource_usage.get(pm_name, {'cpu': 0, 'ram': 0, 'storage': 0, 'vms': []})
                
                scenario_cpu.append(usage['cpu'])
                scenario_ram.append(usage['ram'])
                scenario_storage.append(usage['storage'])
                
                result_text.insert(tk.END, f"\n{pm_name}:\n")
                result_text.insert(tk.END, f"- CPU utilisé: {usage['cpu']:.2f}% ({usage['used_cpu']}/{pm[1]})\n")
                result_text.insert(tk.END, f"- RAM utilisée: {usage['ram']:.2f}% ({usage['used_ram']}/{pm[2]})\n")
                result_text.insert(tk.END, f"- Stockage utilisé: {usage['storage']:.2f}% ({usage['used_storage']}/{pm[3]})\n")
                result_text.insert(tk.END, f"- VMs placées: {', '.join(usage['vms']) if usage['vms'] else 'Aucune'}\n")
                root.update_idletasks()
            
            avg_cpu = sum(scenario_cpu) / len(scenario_cpu) if scenario_cpu else 0
            avg_ram = sum(scenario_ram) / len(scenario_ram) if scenario_ram else 0
            avg_storage = sum(scenario_storage) / len(scenario_storage) if scenario_storage else 0
            
            avg_cpu_usage.append(avg_cpu)
            avg_ram_usage.append(avg_ram)
            avg_storage_usage.append(avg_storage)
            
            result_text.insert(tk.END, f"\nRésumé pour le scénario {num}:\n")
            result_text.insert(tk.END, f"- Nombre de VMs placées: {best_score}\n")
            result_text.insert(tk.END, f"- Nombre de VMs rejetées: {rejected_vms}\n")
            result_text.insert(tk.END, f"- Taux de rejet: {rejection_rate:.2f}%\n")
            result_text.insert(tk.END, f"- CPU moyen utilisé: {avg_cpu:.2f}%\n")
            result_text.insert(tk.END, f"- RAM moyenne utilisée: {avg_ram:.2f}%\n")
            result_text.insert(tk.END, f"- Stockage moyen utilisé: {avg_storage:.2f}%\n")
            root.update_idletasks()
            
            plot_resource_usage(best_solution, pms, num)
        
        if rejection_rates and root.winfo_exists():
            avg_rejection = sum(rejection_rates) / len(rejection_rates)
            global_avg_cpu = sum(avg_cpu_usage) / len(avg_cpu_usage)
            global_avg_ram = sum(avg_ram_usage) / len(avg_ram_usage)
            global_avg_storage = sum(avg_storage_usage) / len(avg_storage_usage)
            
            result_text.insert(tk.END, "\n=== Résultats globaux ===\n")
            result_text.insert(tk.END, f"Taux de rejet moyen: {avg_rejection:.2f}%\n")
            result_text.insert(tk.END, f"CPU moyen utilisé: {global_avg_cpu:.2f}%\n")
            result_text.insert(tk.END, f"RAM moyenne utilisée: {global_avg_ram:.2f}%\n")
            result_text.insert(tk.END, f"Stockage moyen utilisé: {global_avg_storage:.2f}%\n")
            
            plot_rejection_rates(rejection_rates)
        
    except Exception as e:
        if root.winfo_exists():
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"Erreur: {str(e)}\n")
    finally:
        if root.winfo_exists():
            submit_button.config(state=tk.NORMAL)
            load_button.config(state=tk.NORMAL)

# Interface graphique
root = tk.Tk()
root.title("Placement de Machines Virtuelles - Optimisation")
root.geometry("700x700")
root.resizable(False, False)
root.configure(bg='#ADD8E6')

frame = tk.Frame(root, bg='#ADD8E6')
frame.pack(padx=10, pady=10)

for i in range(6):
    frame.grid_rowconfigure(i, weight=1)
frame.grid_columnconfigure(0, weight=1)
frame.grid_columnconfigure(1, weight=1)

tk.Label(frame, text="Nombre de machines physiques (PMs):", bg='#ADD8E6').grid(row=0, column=0, padx=10, pady=5, sticky='w')
entry_n_physiques = tk.Entry(frame)
entry_n_physiques.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

tk.Label(frame, text="Nombre minimum de VMs par scénario:", bg='#ADD8E6').grid(row=1, column=0, padx=10, pady=5, sticky='w')
entry_vm_min = tk.Entry(frame)
entry_vm_min.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

tk.Label(frame, text="Nombre maximum de VMs par scénario:", bg='#ADD8E6').grid(row=2, column=0, padx=10, pady=5, sticky='w')
entry_vm_max = tk.Entry(frame)
entry_vm_max.grid(row=2, column=1, padx=10, pady=5, sticky='ew')

tk.Label(frame, text="Pas pour le nombre de VMs:", bg='#ADD8E6').grid(row=3, column=0, padx=10, pady=5, sticky='w')
entry_step = tk.Entry(frame)
entry_step.grid(row=3, column=1, padx=10, pady=5, sticky='ew')

tk.Label(frame, text="Nombre de scénarios (fichiers VM):", bg='#ADD8E6').grid(row=4, column=0, padx=10, pady=5, sticky='w')
entry_n_scenarios = tk.Entry(frame)
entry_n_scenarios.grid(row=4, column=1, padx=10, pady=5, sticky='ew')

submit_button = tk.Button(frame, text="Générer et Calculer", command=on_submit, bg="#1b019b", fg="white", width=20)
submit_button.grid(row=5, column=0, columnspan=2, pady=10)

load_button = tk.Button(frame, text="Charger scénarios existants", command=load_existing_scenarios, bg="#019b1d", fg="white", width=20)
load_button.grid(row=6, column=0, columnspan=2, pady=10)

result_frame = tk.Frame(root)
result_frame.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)

result_text = scrolledtext.ScrolledText(result_frame, width=80, height=25, bg='#f0f8ff', wrap=tk.WORD)
result_text.pack(fill=tk.BOTH, expand=True)

root.mainloop()