# check and install plugins

required_plugins = %w( vagrant-vbguest vagrant-env vagrant-hostmanager vagrant-timezone)
required_plugins.each do |plugin|
    system "vagrant plugin install #{plugin}" unless Vagrant.has_plugin? plugin
end

# if you want to enable auth proxy 
# vagrant plugin install vagrant-proxyconf

Vagrant.configure(2) do |config|
    # env plugin
    config.env.enable
    # vbguest plugin
    $enable_serial_logging = false
    config.vbguest.auto_update = false
    config.vbguest.no_remote = true

    #hostmanager plugin
    config.hostmanager.enabled = true
    config.hostmanager.manage_host = false
    config.hostmanager.manage_guest = true
    config.hostmanager.ignore_private_ip = false
    config.hostmanager.include_offline = true

    # Setup Proxy plugin infos, only if you have installed the vagrant-proxyconf
    if Vagrant.has_plugin?("vagrant-proxyconf")
        config.proxy.http     = "#{ENV['CORPORATE_HTTP_PROXY']}"
        config.proxy.https    = "#{ENV['CORPORATE_HTTPS_PROXY']}"
        config.proxy.no_proxy = "#{ENV['CORPORATE_NO_PROXY']}"
    end
    
    if Vagrant.has_plugin?("vagrant-timezone")
        config.timezone.value = :host
    end

    # BASTION VM definition

    config.vm.define "BASTION-NODE", primary: true do |lcm_ops_box|
        lcm_ops_box.vm.box = ENV['BASTION_BOX']
        #ansible.vm.box_url = "#$lcm_deployer_box_url"
        lcm_ops_box.vm.hostname = "bastion.#{ENV['INFRA_DOMAIN_NAME']}"
        if ENV['MOUNT_HOST_DIRECTORY']
            lcm_ops_box.vm.synced_folder ENV['HOST_PATH_TO_MOUNT'], "/host"
        end
        lcm_ops_box.vm.network "private_network", ip: "192.168.77.20"
        lcm_ops_box.vm.provider "virtualbox" do |v|
            now = Time.new
            v.name = "BASTION-NODE-#{now.strftime("%H_%M_%d_%m_%Y")}"
            v.linked_clone = true # this configuration will save your time when creating VM 
            v.memory = ENV['BASTION_VM_MEMORY']
            v.cpus = ENV['BASTION_VM_CPU']
        end
    end

    # INFRA VMs definition

    (1..Integer(ENV['NODES_NUMBER'])).each_with_index  do |node_id|
        config.vm.define "#{ENV['NODES_VM_PREFIX']}-#{node_id}" do |lcm_node|
            lcm_node.vm.box = ENV['NODES_BOX']
            lcm_node.vm.hostname = "#{ENV['NODES_VM_PREFIX'].downcase}-#{node_id}.#{ENV['INFRA_DOMAIN_NAME']}"
            lcm_node.vm.network "private_network", ip: "192.168.77.#{30+node_id}"
            lcm_node.vm.provider "virtualbox" do |v|
                now = Time.new
                v.name = "#{ENV['NODES_VM_PREFIX']}-#{node_id}-#{now.strftime("%H_%M_%d_%m_%Y")}"
                v.linked_clone = true
                v.memory = ENV['NODES_VM_MEMORY']
                v.cpus = ENV['NODES_VM_CPU']
            end
        end
    end

end