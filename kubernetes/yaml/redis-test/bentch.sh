kubectl get pods -o wide -n default|grep redis-test|grep -w "$1" |while read name ready status restarts age ip node; do
	echo $name 
	kubectl get pods -o wide -n default|grep redis-test |grep "$2"|while read name2 ready2 status2 restarts2 age2 ip2 node2; do
		result=`kubectl exec -t $name -n default  -- redis-benchmark -n 400 -h $ip2  -t set|grep "requests per second"`
		echo "$node $node2 $result"
	done
done

